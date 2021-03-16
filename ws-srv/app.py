import uvicorn
import socketio
import pika
import sys, os, threading, time
from os import environ


sio = socketio.AsyncServer(async_mode='asgi', logger=True, engineio_logger=True)
app = socketio.ASGIApp(sio)

url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')


@sio.on("connect", namespace="/fib")
async def handle_connect(sid, environ):
    print(f"WebSocket client connected! sid: {sid}", flush=True)

@sio.on("disconnect", namespace="/fib")
async def handle_disconnect(sid):
    print(f"WebSocket client disconnected. sid: {sid}", flush=True)


# WebSocket 'number' message handler
@sio.event(namespace="/fib")
async def number(sid, data):
    global url
    num = data['number']
    print(f"WebSocket 'number' message from: {sid} data: {data} nth fib #: {num}", flush=True)

    #Access the AMQP_URL environment variable and parse it (fallback to rabbit)
    print("Trying to connect to AMQP...", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        return "Failed to connect to AMQP!"

    # We send to 'fib_in'
    channel = connection.channel()
    channel.queue_declare(queue='fib_in')

    channel.basic_publish(exchange='',
                                routing_key='fib_in',
                                body=num)
    connection.close()

    ret = f"Sent Nth fibonacci number: {num} to AMQP 'fib_in' for processing..."
    print(ret, flush=True)
    return ret


# Processor thread used to dequeue response
# from the fib-svc AMQP 'fib_out' queue and
# broadcast a websocket response to /fib ns.
async def processor_thread_function(id):
    global url
    print(f"Processor {id} Trying to connect to AMQP...", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        time.sleep(3)
        await processor_thread_function(id) # KEEP TRYING UNTIL RABBIT IS UP...
    channel = connection.channel()

    # We receive from 'fib_out'
    channel.queue_declare(queue='fib_out')

    async def amqp_receive_callback(ch, method, properties, body):
        print(" [x] Received AMQP message from 'fib_out' queue! data: %r" % body, flush=True)
        try:
            print("Emitting response over WebSocket using broadcast...", flush=True)
            await sio.emit('response', {'number': body}, namespace="/fib")
        except:
            print("Unexpected error:", sys.exc_info()[0], flush=True)
            print("Failed to emit socket.io response!", flush=True)

    # Consume AMQP messages...
    try:
        await channel.basic_consume(amqp_receive_callback,
                                    queue='fib_out')
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise

    print(' [*] Waiting for AMQP messages from fib_out queue...', flush=True)

    try:
        await channel.start_consuming()
    except KeyboardInterrupt:
        await channel.stop_consuming()

    print(f"Processor Thread {id}: finishing", flush=True)



async def main():
    # Start Processor thread
    await sio.start_background_task(processor_thread_function, [1])

    print("Starting Uvicorn server...", flush=True)
    uvicorn.run(app, host='0.0.0.0', port=int(environ.get("PORT", 8081)), log_level="debug")


if __name__ == '__main__':
    asyncio.run(main())  # main loop
