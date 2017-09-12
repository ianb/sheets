import os
import ast
import traceback
import time
import sys
import types
import builtins
import astor
from .htmlize import htmlize, htmlize_repr, htmlize_print, htmlize_short_repr, print_expr
from .datalayer import Analysis, Execution, FileEdit
from .router import send
from . import stdlib

class Environment:

    def __init__(self, path):
        self.path = path
        self.globals = {
            "print": htmlize_print,
            "htmlize": htmlize,
            "htmlize_repr": htmlize_repr,
            "print_expr": print_expr,
            "listdir": stdlib.listdir,
            "__builtins__": __builtins__,
            "FILES": stdlib.FilesDict(self.path),
        }
        for name in stdlib.builtin_names:
            self.globals[name] = getattr(stdlib, name)
        self._cached_analysis = {}

    predefined_names = set(["htmlize", "htmlize_repr", "parsed"])

    def on_open(self):
        for path in os.listdir(self.path):
            if path.endswith(".json"):
                continue
            if not os.path.isfile(os.path.join(self.path, path)):
                continue
            try:
                with open(os.path.join(self.path, path), "r") as fp:
                    content = fp.read()
                command = FileEdit(path, content, external_edit=True)
                send(command)
            except UnicodeDecodeError:
                pass

    def execute(self, filename, content):
        print("Executing", filename)
        output = []
        try:
            parsed = ast.parse(content, filename, mode='exec')
            RewriteExprToPrint().walk(parsed)
            var_inspect = VariableInspector()
            var_inspect.walk(parsed)
            print("varsed used:", sorted(var_inspect.used), "set:", sorted(var_inspect.set), "imported:", var_inspect.imports)
            compiled = compile(parsed, filename, 'exec')
        except:
            output.append(htmlize(traceback.format_exc()))

        def displayhook(value):
            output.append(htmlize_repr(value))

        class Stdout:
            def write(self, content):
                output.append(htmlize(content))

            def writehtml(self, content):
                output.append(content)

        stdout = Stdout()
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
                "type": str(type(local_scope[key])),
                "self_naming": getattr(htmlize_short_repr(local_scope[key]), "self_naming", False),
            })
            for key in local_scope
            if not isinstance(local_scope[key], types.ModuleType))
        command = Execution(
            filename=filename,
            content=content,
            output="".join(str(x) for x in output),
            defines=defines,
            start_time=int(start * 1000),
            end_time=int(end * 1000),
            exec_time=int((end - start) * 1000),
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
            send(Analysis(filename, content, properties))


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
    def pre_Module(self):
        node = self.cur_node
        node.body = [
            self.rewrite_expr(n) if isinstance(n, ast.Expr) else n
            for n in node.body]

    def rewrite_expr(self, node):
        expr_string = astor.to_source(node)
        node_string = ast.Str(s=expr_string)
        new_node = ast.Expr(
            ast.Call(
                func=ast.Name(id='print_expr', ctx=ast.Load()),
                args=[node_string, node.value],
                keywords=[],
                starargs=None,
            )
        )
        ast.fix_missing_locations(new_node)
        return new_node
