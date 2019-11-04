from fiber.core import Sender

class Engine:
    def __init__(self, sio):
        self.sender = Sender(sio)
        self.sio = sio

