import os
import sys
from functools import partial
import traceback
import time

def short_repr(s):
    v = repr(s)
    if len(v) > 20:
        return v[:12] + "..." + v[-5:]
    return v

class Model:

    def __init__(self, env, history):
        self.files = {}
        self.tasks = []
        self.env = env
        self.history = history

    def apply_command(self, command):
        command.apply_to_environment(self.env)
        command.apply_to_model(self)
        self.history.save_command(command)

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

    def on_open(self, router):
        self.history.clean_commands()
        commands = self.history.get_commands()
        if not commands:
            commands = self.env.init_commands()
        for command in commands:
            router.send(command)

class Command:

    attrs = None
    name = None
    _id = None

    def __init__(self, *, id=None):
        self._id = id

    @property
    def id(self):
        # FIXME: I'm not sure timestamps done lazily like this really gives
        # the order we want, but... I guess?
        if not self._id:
            self._id = "c-%s" % time.time()
        return self._id

    @property
    def asJson(self):
        attrs = self.attrs or self.__dict__.keys()
        attrs = [a for a in attrs if a != "_id"]
        data = dict((attr, getattr(self, attr)) for attr in attrs)
        data["command"] = self.name or self.__class__.__name__
        data["id"] = self.id
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

    def scan_back(self, prev_commands):
        pass

class FileEdit(Command):

    def __init__(self, *, filename, content, external_edit=False, id=None):
        super().__init__(id=id)
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

    def scan_back(self, commands):
        for prev in reversed(commands):
            if isinstance(prev, Execution) and prev.filename == self.filename:
                break
            elif isinstance(prev, FileEdit) and prev.filename == self.filename:
                yield prev
            elif isinstance(prev, Analysis) and prev.filename == self.filename:
                yield prev

class FileDelete(Command):

    def __init__(self, *, filename, external_edit=False, id=None):
        super().__init__(id=id)
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

    def __init__(self, *, filename, content, subexpressions=False, id=None):
        super().__init__(id=id)
        self.filename = filename
        self.content = content
        self.subexpressions = subexpressions

    def apply_to_model(self, model):
        model.add_task(("execute_request", self.filename), partial(model.env.execute, self.filename, self.content, self.subexpressions))

    def scan_back(self, commands):
        yield self

class Analysis(Command):

    def __init__(self, *, filename, content, properties, id=None):
        super().__init__(id=id)
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

    def __init__(self, *, filename, content, emitted, defines, start_time, end_time, exec_time, with_subexpressions=False, id=None):
        super().__init__(id=id)
        self.filename = filename
        self.content = content
        self.emitted = emitted
        self.defines = defines
        self.start_time = start_time
        self.end_time = end_time
        self.exec_time = exec_time
        self.with_subexpressions = with_subexpressions

    def apply_to_model(self, model):
        if self.filename not in model.files:
            return
        model.files[self.filename]["execution"] = {
            "content": self.content,
            "emitted": self.emitted,
            "defines": self.defines,
        }

no_default = ['NO DEFAULT']

def hydrate(data, *, if_invalid=no_default):
    me = sys.modules[__name__]
    command_name = data["command"]
    CommandClass = getattr(me, command_name)
    assert issubclass(CommandClass, Command)
    assert CommandClass is not Command
    del data["command"]
    try:
        command = CommandClass(**data)
    except TypeError as e:
        raise
        if if_invalid is no_default:
            raise
        return if_invalid
    return command
