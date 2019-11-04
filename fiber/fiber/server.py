from sanic import Sanic
from sanic_cors import CORS
from socketio import AsyncServer

sio = AsyncServer(async_mode='sanic', cors_allowed_origins=[])
app = Sanic()

app.config['CORS_AUTOMATIC_OPTIONS'] = True
app.config['CORS_SUPPORTS_CREDENTIALS'] = True

CORS(app, automatic_options=True)
sio.attach(app)

