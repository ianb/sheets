import os
from functools import partial
import traceback

def short_repr(s):
    v = repr(s)
    if len(v) > 20:
        return v[:12] + "..." + v[-5:]
    return v

class Model:

    def __init__(self, env):
        self.files = {}
        self.tasks = []
        self.env = env

    def apply_command(self, command):
        command.apply_to_environment(self.env)
        command.apply_to_model(self)

    def add_task(self, key, runner):
        for item in list(self.tasks):
            if item[0] == key:
                self.tasks.remove(item)
        self.tasks.append((key, runner))

    def run_tasks(self):
        while self.tasks:
            runner = self.tasks.pop(0)[1]
            try:
                runner()
            except:
                print("Error running task", runner)
                traceback.print_exc()

class Command:

    attrs = None
    name = None

    @property
    def asJson(self):
        attrs = self.attrs or self.__dict__.keys()
        data = dict((attr, getattr(self, attr)) for attr in attrs)
        data["command"] = self.name or self.__class__.__name__
        return data

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            " ".join(
                '%s=%s' % (name, short_repr(value)) for name, value in sorted(self.asJson.items())
                if name != "command"),
        )

    def apply_to_model(self, model):
        pass

    def apply_to_environment(self, env):
        pass

class FileEdit(Command):

    def __init__(self, filename, content, external_edit=False):
        self.filename = filename
        self.content = content
        self.external_edit = external_edit

    def apply_to_environment(self, env):
        if self.external_edit:
            # Then it is already applied to the environment
            return
        filename = os.path.abspath(os.path.join(env.path, self.filename))
        if not filename.startswith(env.path):
            raise Exception("Bad file: {} resolves to {}, not in base {}".format(self.filename, filename, env.path))
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, "w") as fp:
            fp.write(self.content)

    def apply_to_model(self, model):
        if self.filename not in model.files:
            model.files[self.filename] = {}
        model.files[self.filename]["content"] = self.content
        model.add_task(("analyze", self.filename), partial(model.env.analyze, self.filename, self.content))

class FileDelete(Command):

    def __init__(self, filename, external_edit=False):
        self.filename = filename
        self.external_edit = external_edit

    def apply_to_environment(self, env):
        if self.external_edit:
            return
        filename = os.path.abspath(os.path.join(env.path, self.filename))
        if not filename.startswith(env.path):
            raise Exception("Bad file: {} resolves to {}, not in base {}".format(self.filename, filename, env.path))
        if os.path.exists(filename):
            os.unlink(filename)
        else:
            print("Warning: delete of file {} resolves to {}, which does not exists".format(
                self.filename, filename))

    def apply_to_model(self, model):
        if self.filename in model.files:
            del model.files[self.filename]

class ExecutionRequest(Command):

    def __init__(self, filename, content):
        self.filename = filename
        self.content = content

    def apply_to_model(self, model):
        model.add_task(("execute_request", self.filename), partial(model.env.execute, self.filename, self.content))

class Analysis(Command):

    def __init__(self, filename, content, properties):
        self.filename = filename
        self.content = content
        self.properties = properties

    def apply_to_model(self, model):
        if self.filename not in model.files:
            return
        model.files[self.filename]["analysis"] = {
            "content": self.content,
            "properties": self.properties,
        }

class Execution(Command):

    def __init__(self, *, filename, content, output, defines, start_time, end_time, exec_time):
        self.filename = filename
        self.content = content
        self.output = output
        self.defines = defines
        self.start_time = start_time
        self.end_time = end_time
        self.exec_time = exec_time

    def apply_to_model(self, model):
        if self.filename not in model.files:
            return
        model.files[self.filename]["execution"] = {
            "content": self.content,
            "output": self.output,
            "defines": self.defines,
        }
