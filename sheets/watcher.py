import types
import inspect
from .typedispatch import TypeDispatcher
from .jsonify import jsonify, jsonify_print

def watch(obj, label=None):
    jsonify_print(Watcher(obj, label))
    return obj

watch.collector = TypeDispatcher()

class Watcher:

    def __init__(self, obj, label):
        self.obj = obj
        self.label = label

    def _sheets_json_(self):
        d = {
            "type": "watch",
            "obj": jsonify(self.obj),
        }
        if self.label:
            d["label"] = self.label
        if not isinstance(self.obj, type):
            # Everything but classes gets their classes inspected
            d["object_class"] = jsonify(self.__class__(type(self.obj), None))
        for extra_data in reversed(watch.collector.collect(self.obj)):
            if extra_data:
                d.update(extra_data)
        return d

@watch.collector(object)
def watch_object(o):
    if False and isinstance(o, type):
        return {}
    d = {
        "attributes": [
            ("." + name, jsonify(getattr(o, name)))
            for name in dir(o)
            if not hasattr(object, name) and name != "__weakref__"],
    }
    doc = inspect.getdoc(o)
    if doc:
        d["doc"] = {"type": "docstring", "docstring": doc}
    return d

@watch.collector(type)
def watch_class(o):
    pass

@watch.collector((types.FunctionType, types.MethodType))
def watch_func(o):
    pass

@watch.collector(types.ModuleType)
def watch_module(o):
    pass
