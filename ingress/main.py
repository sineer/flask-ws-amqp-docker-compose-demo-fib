import sys

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    message = "Hello World from Flask in a uWSGI Nginx Docker container with Python {} (default)".format(
        version
    )
    return message


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)


# from os import environ

# import socketio
# import uvicorn
# import requests

# from fastapi import Body, FastAPI
# from fastapi.responses import HTMLResponse


# app = FastAPI()

# sio = socketio.AsyncServer(
#     async_mode='asgi',
#     cors_allowed_origins='*'
# )

# ws = socketio.ASGIApp(
#     socketio_server=sio,
#     other_asgi_app=app,
#     socketio_path='/socket.io/'
# )

# connected = False

# MY_NAMESPACE = "/fib"
# DATA_EVENT_NAME = "number"
# HANDLER_ADDRESS = (
#     environ["HANDLER_ADDRESS"]
#     if "HANDLER_ADDRESS" in environ
#     else "http://0.0.0.0:5000/"
# )

# WS_ADDRESS = (
#     environ["WS_ADDRESS"]
#     if "WS_ADDRESS" in environ
#     else "http://0.0.0.0:5001/"
# )


# @sio.on("connect", namespace="/fib")
# def handle_connect(sid, environ):
#     print(f"WebSocket client connected {sid}", flush=True)

# @sio.on("disconnect", namespace="/fib")
# def handle_disconnect(sid):
#     print(f"WebSocket client disconnected {sid}", flush=True)


# @app.get("/", response_class=HTMLResponse)
# def handle_index():
# #    global connected
# #    if not connected:
# #        print("Connecting WebSocket Client to server address: " + WS_ADDRESS)
# #        sio.connect(WS_ADDRESS + socket, namespaces=[MY_NAMESPACE])
# #        # XXX TRY CATCH!?
# #        connected = True
#     req = requests.get(HANDLER_ADDRESS, auth=('user', 'pass'))
#     return req.text


# @app.post("/fib")
# async def fib_number(number: int = Body(...)):
#     print("emit nth fib_number: " + str(number))
#     sio.emit(DATA_EVENT_NAME, {'number': number}, namespace=MY_NAMESPACE)
#     return "..."


# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=int(environ.get("PORT", 8081)),
#     )
