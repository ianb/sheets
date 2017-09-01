import json
import traceback
from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

sockets = []
listeners = []
listeners_open = []

def send(message):
    data = json.dumps(message)
    for socket in sockets:
        socket.send(data)

def listen(callback):
    listeners.append(callback)

def listen_open(callback):
    listeners_open.append(callback)

class WebSocketHandler(WebSocket):

    def opened(self):
        sockets.append(self)
        for listener_open in listeners_open:
            try:
                listener_open()
            except:
                print("Error in listener_open", listener_open)
                traceback.print_exc()
                continue

    def closed(self, code, reason=None):
        sockets.remove(self)

    def received_message(self, message):
        try:
            data = json.loads(str(message))
        except:
            print("Bad JSON data: %s" % message)
            raise
        for listener in listeners:
            try:
                listener(data)
            except:
                print("Error in", listener, ":")
                traceback.print_exc()

    # self.send(payload, binary=False)

def run_server(port):
    server = make_server('', port, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=WebSocketHandler))
    server.initialize_websockets_manager()
    server.serve_forever()
