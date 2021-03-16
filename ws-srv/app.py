import asyncio
import uvicorn
import socketio
import pika
import sys, os, threading, time
from os import environ
from uvicorn.config import Config
from uvicorn.main import Server

# heh no comment... Still don't work too! Maybe because I must use uvicorn[standard] ?
# https://github.com/miguelgrinberg/python-socketio/issues/282
from uvicorn.loops.uvloop import uvloop_setup


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

    while True:
        try:
            connection = pika.BlockingConnection(params)
            break
        except:
            time.sleep(3)
            continue # KEEP TRYING UNTIL RABBIT IS UP...
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
        channel.basic_consume(queue='fib_out',
                              on_message_callback=amqp_receive_callback)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise

    print(' [*] Waiting for AMQP messages from fib_out queue...', flush=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    print(f"Processor Thread {id}: finishing", flush=True)



# Set up the event loop...
# async def start_processor():
#     print("Starting Processor...", flush=True)
#     await sio.start_background_task(processor_thread_function, [1])

# async def start_uvicorn():
#     print("Starting Uvicorn Server...", flush=True)
#     uvicorn.run(app, host='0.0.0.0', port=int(environ.get("PORT", 5001)), log_level="debug")

# async def main(loop):
#     bg_task = loop.create_task(start_processor())
#     uv_task = loop.create_task(start_uvicorn())
#     await asyncio.wait([bg_task, uv_task])

if __name__ == '__main__':
    # uvloop_setup()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(loop))
    # loop.close()

    class CustomServer(Server):
        def install_signal_handlers(self):
            pass

    config = Config(app,
                    host='0.0.0.0',
                    port=int(environ.get("PORT", 5001)),
                    log_level="debug",
                    loop="asyncio")

    server = CustomServer(config=config)

    print("Starting Uvicorn Server...", flush=True)
    #uvicorn.run(app, host='0.0.0.0', port=int(environ.get("PORT", 5001)), log_level="debug")
    thread = threading.Thread(target=server.run)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    print("Custom Uvicorn Server Thread Started!")

    asyncio.run(processor_thread_function(1))
    print("Processor Thread Started!")

    # NOTE: So this was one last attempt but I am forced to use asyncio in the end because
    #       of sio.emit being async... Now my "custom" Uvicorn server starts but it's the
    #       processor thread that's hung up and does not try to connect to AMQP.

    thread.join()
