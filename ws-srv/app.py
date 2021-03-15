import uvicorn
import socketio
import pika, sys, os
from os import environ


sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio)


@sio.on("connect", namespace="/fib")
def handle_connect(sid, environ):
    print(f"WebSocket client connected! sid: {sid}", flush=True)

@sio.on("disconnect", namespace="/fib")
def handle_disconnect(sid):
    print(f"WebSocket client disconnected. sid: {sid}", flush=True)


@sio.event(namespace="/fib")
def number(sid, data):
    num = data['number']
    print(f"WebSocket 'number' message from: {sid} data: {data} nth fib #: {num}", flush=True)

    #Access the AMQP_URL environment variable and parse it (fallback to rabbit)
    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    print("Trying to connect to AMQP", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise
    channel = connection.channel()
    channel.exchange_declare(exchange='fibs', exchange_type='fanout')
    channel.queue_declare(queue='fib_in')
    channel.basic_publish(
        exchange='fibs',
        routing_key='fib_in',
        body=num)
    channel.queue_bind(exchange='fibs',
                       queue='fib_in')
    connection.close()
    ret = f"Sent Nth fibonacci number: {num} to AMQP 'fib_in' for processing..."
    print(ret, flush=True)
    return ret

# XXX Listen for the response from fib-svc (AMQP 'fib_out'Queue)


if __name__ == '__main__':
    print("Starting Uvicorn server...", flush=True)
    uvicorn.run(app, host='0.0.0.0', port=int(environ.get("PORT", 8081)), log_level="debug")
