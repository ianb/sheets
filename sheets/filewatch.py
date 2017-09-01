import os
import atexit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .datalayer import FileEdit, FileDelete
from .router import send

def watch(env, model):
    return
    event_handler = FileStoreEventHandler(env, model)
    observer = Observer()
    observer.schedule(event_handler, env.path, recursive=True)
    observer.start()
    atexit.register(observer.stop)

class FileStoreEventHandler(FileSystemEventHandler):

    def __init__(self, env, model):
        self.env = env
        self.model = model

    def name_from_path(self, path):
        path = os.path.abspath(os.path.join(self.env.path, path))
        if not path.startswith(os.path.abspath(self.env.path)):
            print("Unexpected update of file {} not under {}".format(path, self.env.path))
            raise Exception("Bad file: {}".format(path))
        path = path[len(os.path.abspath(self.env.path)):].lstrip("/")
        return path

    def on_modified(self, event):
        if event.is_directory:
            return
        filename = event.src_path
        name = self.name_from_path(filename)
        with open(filename, "r") as fp:
            content = fp.read()
        expected = self.model.files.get(name)
        if expected and expected["content"] == content:
            return
        send(FileEdit(filename=name, content=content, external_edit=True))

    on_created = on_modified

    def on_moved(self, event):
        if event.is_directory:
            return
        name = self.name_from_path(event.src_path)
        dest_name = self.name_from_path(event.dest_path)
        if self.model.files.get(name):
            send(FileDelete(filename=name), external_edit=True)
        with open(event.dest_path, "r") as fp:
            content = fp.read()
        expected = self.model.files.get(dest_name)
        if not expected or expected["content"] != content:
            send(FileEdit(filename=dest_name, content=content, external_edit=True))

    def on_deleted(self, event):
        if event.is_directory:
            return
        name = self.name_from_path(event.src_path)
        if self.model.files.get(name):
            send(FileDelete(filename=name, external_edit=True))
