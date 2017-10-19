import os
import ast
import traceback
import time
import sys
import types
import builtins
import collections
import astor
from .htmlize import htmlize, htmlize_repr, htmlize_short_repr
from .jsonify import jsonify, jsonify_print, jsonify_print_expr
from .datalayer import Analysis, Execution, FileEdit
from .router import send
from . import stdlib

def now():
    return int(time.time() * 1000)

class Environment:

    def __init__(self, path):
        self.path = path
        self.globals = {
            "htmlize": htmlize,
            "htmlize_repr": htmlize_repr,
            "print": jsonify_print,
            "print_expr": jsonify_print_expr,
            "jsonify": jsonify,
            "jsonify_print": jsonify_print,
            "listdir": stdlib.listdir,
            "__builtins__": __builtins__,
            "FILES": stdlib.FilesDict(self.path),
        }
        for name in stdlib.builtin_names:
            self.globals[name] = getattr(stdlib, name)
        self._cached_analysis = {}

    predefined_names = set(["htmlize", "htmlize_repr", "parsed"])

    def init_commands(self):
        """Returns a list of commands that represent the existing state of the
        filesystem"""
        for path in os.listdir(self.path):
            if path.endswith(".json"):
                continue
            if not os.path.isfile(os.path.join(self.path, path)):
                continue
            try:
                with open(os.path.join(self.path, path), "r") as fp:
                    content = fp.read()
                yield FileEdit(filename=path, content=content, external_edit=True)
            except UnicodeDecodeError:
                pass

    def execute(self, filename, content, subexpressions=False):
        print("Executing", filename, subexpressions)
        stdout = Stdout()
        compiled = None
        try:
            parsed = ast.parse(content, filename, mode='exec')
            RewriteExprToPrint(subexpressions).walk(parsed)
            var_inspect = VariableInspector()
            var_inspect.walk(parsed)
            print("varsed used:", sorted(var_inspect.used), "set:", sorted(var_inspect.set), "imported:", var_inspect.imports)
            compiled = compile(parsed, filename, 'exec')
        except:
            stdout.write(traceback.format_exc())

        def displayhook(value):
            stdout.write_repr(value)

        orig_displayhook = sys.displayhook
        sys.displayhook = displayhook
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        sys.stdout = stdout
        sys.stderr = stdout
        self.globals["parsed"] = parsed
        self.globals["ast"] = ast
        globals_before = self.globals.copy()
        start = time.time()
        try:
            try:
                if compiled:
                    exec(compiled, self.globals)
            except:
                traceback.print_exc()
        finally:
            end = time.time()
            sys.dipslayhook = orig_displayhook
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
        local_scope = dict(
            (name, value)
            for name, value in self.globals.items()
            if name not in globals_before or globals_before[name] is not value)
        defines = dict(
            (key, {
                "repr": str(htmlize_short_repr(local_scope[key])),
                "json": jsonify(local_scope[key]),
                "type": str(type(local_scope[key])),
                "self_naming": getattr(htmlize_short_repr(local_scope[key]), "self_naming", False),
            })
            for key in local_scope
            if not isinstance(local_scope[key], types.ModuleType))
        command = Execution(
            filename=filename,
            content=content,
            output="".join(str(x) for x in stdout.html_output),
            emitted=stdout.emitted,
            defines=defines,
            start_time=int(start * 1000),
            end_time=int(end * 1000),
            exec_time=int((end - start) * 1000),
            with_subexpressions=subexpressions,
        )
        send(command)

    def analyze(self, filename, content):
        print("Analyzing", filename)
        properties = {}
        try:
            parsed = ast.parse(content, filename, mode='exec')
            var_inspect = VariableInspector()
            var_inspect.walk(parsed)
        except:
            return
            properties["parse_error"] = str(htmlize(traceback.format_exc()))
        else:
            properties = var_inspect.json
        if properties != self._cached_analysis.get(filename):
            self._cached_analysis[filename] = properties
            send(Analysis(filename=filename, content=content, properties=properties))


class VariableInspector(astor.TreeWalk):

    builtin_names = dir(builtins)

    def init_variables(self):
        self.used = set()
        self.set = set()
        self.imports = set()
        self.in_target = False

    @property
    def json(self):
        used = set(self.used)
        for key in self.builtin_names:
            used.discard(key)
        for key in self.set:
            used.discard(key)
        for key in Environment.predefined_names:
            used.discard(key)
        return {
            "variables_used": list(used),
            "variables_set": list(self.set),
            "imports": list(self.imports)
        }

    def pre_arg(self):
        self.set.add(self.cur_node.arg)

    def pre_Name(self):
        if self.in_target:
            # Actually this is a set
            self.set.add(self.cur_node.id)
        else:
            self.used.add(self.cur_node.id)

    def pre_For(self):
        self.process_assignment(self.cur_node.target)

    def pre_Assign(self):
        self.process_assignment(self.cur_node.targets)

    def pre_withitem(self):
        self.process_assignment(self.cur_node.optional_vars)

    def pre_ExceptHandler(self):
        if self.cur_node.name:
            self.set.add(self.cur_node.name)

    def pre_alias(self):
        # Used in imports
        name = self.cur_node.asname or self.cur_node.name
        name = name.split(".")[0]
        self.set.add(name)
        self.imports.add(name)

    def pre_FunctionDef(self):
        self.set.add(self.cur_node.name)

    def pre_ListComp(self):
        self.process_assignment(self.cur_node.elt)

    def process_assignment(self, item):
        if isinstance(item, list):
            for x in item:
                self.process_assignment(x)
            return
        old_in_target = self.in_target
        self.in_target = True
        try:
            self.walk(item)
        finally:
            self.in_target = old_in_target

class RewriteExprToPrint(astor.TreeWalk):

    expr_node_types = """
    UnaryOp
    BinOp
    BoolOp
    Compare
    Call
    IfExp
    Attribute
    Subscript
    ListComp SetComp GeneratorExp DictComp
    """.split()
    # Skipped:
    #  UAdd USub Not Invert
    #  Add Sub Mult Div FloorDiv Mod Pow LShift RShift BitOr BitXor BitAnd MatMult
    #  And Or
    #  Eq NotEq Lt Gt GtE Is IsNot In NotIn
    #  Index Slice ExtSlice

    def __init__(self, subexpressions=False):
        self.subexpressions = subexpressions
        self.id_counter = 0
        astor.TreeWalk.__init__(self)
        if self.subexpressions:
            for method in self.expr_node_types:
                self.pre_handlers[method] = self.save_node_name
                self.post_handlers[method] = self.fixup_subexpressions
            del self.post_handlers['Module']

    def post_Name(self):
        if not self.subexpressions:
            return
        if isinstance(self.cur_node.ctx, ast.Load):
            self.replace(self.rewrite_expr(self.cur_node))

    def post_Module(self):
        node = self.cur_node
        node.body = [
            self.rewrite_expr(n) if isinstance(n, ast.Expr) else n
            for n in node.body]

    def save_node_name(self):
        self.cur_node.astor_repr = astor.to_source(self.cur_node)

    def fixup_subexpressions(self):
        new_node = self.rewrite_expr(self.cur_node, self.cur_node.astor_repr)
        self.replace(new_node)

    def rewrite_expr(self, node, expr_string=None):
        if expr_string is None:
            expr_string = astor.to_source(node)
        node_string = ast.Str(s=expr_string)
        self.id_counter += 1
        if isinstance(node, ast.Expr):
            new_node = ast.Expr(
                ast.Call(
                    func=ast.Name(id='print_expr', ctx=ast.Load()),
                    args=[node_string, node.value, ast.Num(n=self.id_counter)],
                    keywords=[],
                    starargs=None,
                )
            )
            new_node.is_print_expr = True
        else:
            new_node = ast.Call(
                func=ast.Name(id='print_expr', ctx=ast.Load()),
                args=[node_string, node, ast.Num(n=self.id_counter)],
                keywords=[],
                starargs=None,
            )
            new_node.is_print_expr = True
        ast.fix_missing_locations(new_node)
        return new_node


class Stdout:

    total_exprs_limit = 100
    expr_limit = 10

    def __init__(self):
        self.html_output = []
        self.emitted = []
        self.total_exprs_printed = 0
        self.exprs_printed = collections.Counter()

    def write(self, content):
        h = htmlize(content)
        self.html_output.append(h)
        self.emitted.append({
            "type": "print",
            "time": now(),
            "parts": [{"type": "str", "str": content, "html": str(h)}],
        })

    def writehtml(self, content):
        self.html_output.append(content)
        self.emitted.append({
            "type": "explicit_html",
            "time": now(),
            "html": str(content),
        })

    def writejson(self, json):
        assert json.get("type"), "JSON objects must have a type"
        json.setdefault("time", now())
        self.emitted.append(json)

    def write_repr(self, o):
        h = htmlize_repr(o)
        self.html_output.append(h)
        self.emitted.append({
            "type": "plain_repr",
            "time": now(),
            "html": str(h)
        })

    def flush(self):
        pass
