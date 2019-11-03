from socketio import AsyncServer
from sanic import Sanic
from sanic_cors import CORS

sio = AsyncServer(async_mode="sanic")
app = Sanic()
app.config['CORS_AUTOMATIC_OPTIONS'] = True
CORS(app, automatic_options=True)
sio.attach(app)

