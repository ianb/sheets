from . import datalayer
from . import server

a_router = None

class Router:

    def __init__(self, *, env, model):
        self.env = env
        self.model = model

    def send(self, command):
        assert isinstance(command, datalayer.Command)
        self.model.apply_command(command)
        j = command.asJson
        server.send(j)
        self.model.run_tasks()

    def incoming(self, data):
        command = datalayer.hydrate(data)
        self.model.apply_command(command)
        self.model.run_tasks()

    def on_open(self):
        self.model.on_open(self)
        self.model.run_tasks()

    def register(self):
        global a_router
        a_router = self
        server.listen(self.incoming)
        server.listen_open(self.on_open)
        from . import filewatch
        filewatch.watch(self.env, self.model)

def send(command):
    print("Sending:", command)
    a_router.send(command)
