import sys
import importlib

watchers = {
    "keras": "sheets.support.keras",
    "PIL": "sheets.support.PIL",
}

class WatchPaths:

    def find_spec(self, fullname, path, target=None):
        """Called when an import happens. Note this is only to watch imports,
        not to change what is imported"""
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
                importlib.import_module(support_module)
        return None

def activate():
    sys.meta_path.insert(0, WatchPaths())
