import keras
import functools
from io import StringIO
from ..jsonify import jsonify

@jsonify.register(keras.engine.topology.Container)
def jsonify_keras_container(model):
    fp = StringIO()
    print_fn = functools.partial(print, file=fp)
    model.summary(print_fn=print_fn)
    return {
        "type": "dump",
        "repr": repr(model),
        "dump": fp.getvalue(),
    }
