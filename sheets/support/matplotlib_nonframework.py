"""
This just lets matplotlib be imported in non-Framework builds. We aren't going
to let matplotlib open windows anyway, so this support isn't needed.
"""
import sys
import types

def make_class(class_name, *methods):
    class NullClass:
        name = class_name

        def __init__(self, *args, **kw):
            pass

    def null_method(*args, **kw):
        pass

    for method in methods:
        setattr(NullClass, method, null_method)
    setattr(_macosx, class_name, NullClass)
_macosx = types.ModuleType("matplotlib.backends._macosx")
make_class("Timer")
make_class("FigureCanvas", "invalidate")
make_class("FigureManager")
make_class("NavigationToolbar2")
sys.modules["matplotlib.backends._macosx"] = _macosx
