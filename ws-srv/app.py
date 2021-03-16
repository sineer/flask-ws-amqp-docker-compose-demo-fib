import uvicorn
import socketio
import pika
import sys, os, threading, time
from os import environ


sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio)
url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')


@sio.on("connect", namespace="/fib")
def handle_connect(sid, environ):
    print(f"WebSocket client connected! sid: {sid}", flush=True)

@sio.on("disconnect", namespace="/fib")
def handle_disconnect(sid):
    print(f"WebSocket client disconnected. sid: {sid}", flush=True)


# WebSocket 'number' message handler
@sio.event(namespace="/fib")
def number(sid, data):
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

    channel = connection.channel()
    channel.exchange_declare(exchange='fib',
                             exchange_type='fanout')

    # We send to 'fib_in'
    channel.queue_declare(queue='fib_in')
    channel.basic_publish(
        exchange='fib',
        routing_key='fib_in',
        body=num)
    channel.queue_bind(exchange='fib',
                       queue='fib_in')
    connection.close()

    ret = f"Sent Nth fibonacci number: {num} to AMQP 'fib_in' for processing..."
    print(ret, flush=True)
    return ret


# Processor thread used to dequeue response
# from the fib-svc AMQP 'fib_out' queue and
# broadcast a websocket response to /fib ns.
def processor_thread_function(id):
    global url
    print(f"Processor {id} Trying to connect to AMQP...", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        time.sleep(3)
        processor_thread_function(id) # KEEP TRYING UNTIL RABBIT IS UP...
    channel = connection.channel()

    # We receive from 'fib_out'
    channel.queue_declare(queue='fib_out')

    def amqp_receive_callback(ch, method, properties, body):
        print(" [x] Received AMQP message from 'fib_out' queue! data: %r" % body, flush=True)
        # XXX emit_response(...)

    # Consume AMQP messages...
    try:
        channel.basic_consume(amqp_receive_callback,
                              queue='fib_out',
                              no_ack=False)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise

    print(' [*] Waiting for AMQP messages from fib_out queue...', flush=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    print(f"Processor Thread {id}: finishing", flush=True)



if __name__ == '__main__':

    # Start Processos thread
    processor = threading.Thread(target=processor_thread_function, args=(1,), daemon=False)
    processor.start()

    print("Starting Uvicorn server...", flush=True)
    uvicorn.run(app, host='0.0.0.0', port=int(environ.get("PORT", 8081)), log_level="debug")
