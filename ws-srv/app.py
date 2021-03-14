from os import environ

import uvicorn

import socketio

sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio)


@sio.on("connect", namespace="/fib")
def handle_connect(sid, environ):
    print(f"WebSocket client connected {sid}", flush=True)

@sio.on("disconnect", namespace="/fib")
def handle_disconnect(sid):
    print(f"WebSocket client disconnected {sid}", flush=True)


@sio.event(namespace="/fib")
def number(sid, message):
    print(f"fib_message! {sid} {message}", flush=True)
#    sio.emit('my_response', {'data': message['data']}, room=sid)


if __name__ == '__main__':
    print("Starting Uvicorn server...", flush=True)
    uvicorn.run(app, host='0.0.0.0', port=int(environ.get("PORT", 8081)), log_level="debug")
