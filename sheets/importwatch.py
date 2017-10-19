"""
Watch for modules being imported, and import supporting modules at the same time.

Add items to the watchers variable: each key is a module name, and the value
is a module or modules that should be imported at the same time.
"""
import sys
import importlib

watchers = {
    "keras": "sheets.support.keras",
    "PIL": "sheets.support.PIL",
    "matplotlib": ["sheets.support.matplotlib_nonframework", "sheets.support.matplotlib"]
}

class WatchPaths:

    in_import = False

    def find_spec(self, fullname, path, target=None):
        """Called when an import happens. Note this is only to watch imports,
        not to change what is imported"""
        if self.in_import:
            return None
        parts = fullname.split(".")
        module_parts = []
        for part in parts:
            module_parts.append(part)
            module = ".".join(module_parts)
            if module not in watchers:
                continue
            other_import = watchers[module]
            if isinstance(other_import, str):
                other_import = [other_import]
            for support_module in other_import:
                if support_module in sys.modules:
                    continue
                sys.__stderr__.write("Importing complementary module %s (for %s)\n" % (support_module, module))
                self.in_import = True
                try:
                    importlib.import_module(support_module)
                finally:
                    self.in_import = False
        return None

def activate():
    sys.meta_path.insert(0, WatchPaths())
