import keras
import functools
from io import StringIO
from ..htmlize import htmlize
from tempita import html_quote

@htmlize.register(keras.engine.topology.Container)
def htmlize(model):
    fp = StringIO()
    print_fn = functools.partial(print, file=fp)
    model.summary(print_fn=print_fn)
    return '<pre>%s</pre>' % html_quote(fp.getvalue())
