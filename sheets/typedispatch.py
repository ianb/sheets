"""
Usage:

from sheets.typedispatch import TypeDispatcher
some_dispatch = TypeDispatcher()

@some_dispatch(int)
def handle_int(i):
    return str(i ** 2)

@some_dispatch(object)
def handle_ob(ob):
    return repr(ob)

print(some_dispatch.funcs_for_type(type(2)))
# ==> [<function handle_int>, <function handle_ob>]
print(some_dispatch.collect(2))
# ==> ['4', '2']
"""

class TypeDispatcher:

    def __init__(self, default=None):
        self.registered = []
        if default is not None:
            self.registered.append(object, default)

    def __call__(self, types):
        def decorator(func):
            self.register_function(types, func)
            return func
        return decorator

    def register_function(self, types, func):
        if not isinstance(types, tuple):
            types = (types,)
        for t in types:
            self.registered.append((t, func))

    def funcs_for_type(self, t):
        options = [
            (f, f_type) for f_type, f in self.registered
            if issubclass(t, f_type)]
        options_ranked = [
            (len([f_type for sub_f, f_type in options if issubclass(main_type, f_type)]), f)
            for f, main_type in options]
        options_ranked.sort(key=lambda x: -x[0])
        return [f for c, f in options_ranked]

    def collect(self, ob, *args, **kw):
        return [f(ob, *args, **kw) for f in self.funcs_for_type(type(ob))]
