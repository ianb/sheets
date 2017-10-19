import sys
import ast
import astor
import time
import types
import builtins
from functools import singledispatch

builtins_set = set()
for _name in dir(builtins):
    try:
        builtins_set.add(getattr(builtins, _name))
    except TypeError:
        pass

def jsonify_plain(o, show_repr=False):
    if show_repr:
        return {
            "type": "plain_repr",
            "repr": repr(o),
        }
    else:
        return {
            "type": "plain_str",
            "str": str(o),
        }

jsonify_dispatched = singledispatch(jsonify_plain)

def jsonify(o, show_repr=False):
    if hasattr(o, "_sheets_json_"):
        j = o._sheets_json_()
        return j
    if hasattr(o, "_repr_html_"):
        h = o._repr_html_()
        if h is None:
            print("Warning: object %r._repr_html_() returned None")
            return jsonify_plain(o)
        return {
            "type": "explicit_html",
            "html": h,
        }
    j = jsonify_dispatched(o, show_repr=show_repr)
    j["show_repr"] = show_repr
    j["time"] = int(time.time() * 1000)
    return j

def jsonify_repr(o):
    return jsonify(o, show_repr=True)

jsonify.register = jsonify_dispatched.register
jsonify.dispatch = jsonify_dispatched.dispatch

@jsonify.register(types.FunctionType)
def htmlize_func(x, show_repr=False):
    return {
        "type": "FunctionType",
        "name": x.__qualname__,
        # FIXME: include scope or module or some other info
    }

@jsonify.register(type)
def jsonify_class(x, show_repr=False):
    d = {
        "type": "class",
        "name": x.__name__,
    }
    if not show_repr:
        d["dir"] = dir(x)
        d["bases"] = [c.__name__ for c in x.__bases__]
    return d

@jsonify.register((list, tuple))
def jsonify_list_tuple(x, show_repr=False):
    if isinstance(x, list):
        json_type = "list"
    else:
        json_type = "tuple"
    contents = [jsonify(child, show_repr=show_repr) for child in x]
    return {
        "type": json_type,
        "contents": contents,
    }

@jsonify.register(dict)
def jsonify_dict(x, show_repr=False):
    contents = []
    for key, value in x.items():
        contents.append([jsonify(key, show_repr=True), jsonify(value, show_repr=show_repr)])
    return {
        "type": "dict",
        "contents": contents,
    }

@jsonify.register(str)
def jsonify_str(x, show_repr=False):
    return {
        "type": "str",
        "str": str(x),
    }

@jsonify.register(ast.AST)
def jsonify_ast(x, show_repr=False):
    return {
        "type": "dump",
        "repr": repr(x),
        "dump": astor.dump(x, indentation='  '),
    }

def jsonify_print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    d = {
        "type": "print",
        "parts": []
    }
    if sep != " ":
        d["sep"] = sep
    if end != "\n":
        d["end"] = end
    # FIXME: for some reason there's typically a wrapper on sys.stdout
    file = sys.stdout
    for o in objects:
        sys.__stdout__.write(repr(["Got a part", o, type(o), jsonify(o), jsonify.dispatch(type(o))]) + "\n")
        d["parts"].append(jsonify(o))
    file.writejson(d)

def jsonify_print_expr(expr_string, expr_value, expr_id=None):
    if expr_value is None:
        # Don't print anything, just like the CLI
        return None
    if print_expr_should_ignore(expr_string, expr_value):
        return expr_value
    stdout = sys.stdout
    if stdout.total_exprs_printed > stdout.total_exprs_limit or (expr_id and stdout.exprs_printed[expr_id] > stdout.expr_limit):
        return expr_value
    stdout.total_exprs_printed += 1
    if expr_id:
        stdout.exprs_printed[expr_id] += 1
    d = {
        "type": "print_expr",
        "expr_string": expr_string,
    }
    if stdout.total_exprs_printed > stdout.total_exprs_limit:
        d["remaining_suppressed"] = True
    if expr_id and stdout.exprs_printed[expr_id] > stdout.expr_limit:
        d["this_suppressed"] = True
    d["expr_value"] = jsonify(expr_value)
    stdout.writejson(d)
    return expr_value

def print_expr_should_ignore(expr, value):
    """Returns True if given the expression name (expr) and value, it would be
    too boring to print out the expression"""
    if type(value) in (types.ModuleType, types.BuiltinFunctionType):
        # Modules and built-in functions are too boring
        return True
    if isinstance(value, type):
        class_name = value.__name__.split(".")[-1]
        expr_name = expr.split(".")[-1]
        if class_name == expr_name:
            return True
    if isinstance(value, types.MethodType):
        method_name = value.__name__
        prop_name = expr.split(".")[-1]
        if method_name == prop_name:
            return True
    try:
        if value in builtins_set:
            return True
    except TypeError:
        pass
    return False
