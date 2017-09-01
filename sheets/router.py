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
        command_name = data["command"]
        CommandClass = getattr(datalayer, command_name)
        assert issubclass(CommandClass, datalayer.Command)
        assert CommandClass is not datalayer.Command
        del data["command"]
        command = CommandClass(**data)
        self.model.apply_command(command)
        self.model.run_tasks()

    def on_open(self):
        self.env.on_open()
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
