from contextlib import contextmanager
from io import BytesIO
from tempita import html_quote
from webob import Response
from ..http import http_objects
from matplotlib import pyplot
from ..env import add_global

# Just a way to save stuff for now
save_these = []

@contextmanager
def make_figure(use_figure=None):
    prev_figure = pyplot.gcf()
    if use_figure:
        new_figure = use_figure
        pyplot.figure(use_figure.number)
    else:
        new_figure = pyplot.figure()
    yield new_figure
    if prev_figure:
        pyplot.figure(prev_figure.number)

def get_svg(figure):
    with make_figure(figure):
        fp = BytesIO()
        pyplot.savefig(fp, format="svg")
        return fp.getvalue()

class Plot:
    def __init__(self, data):
        self.data = data
        self.figure = None

    def init_data(self):
        if self.figure:
            self.figure.close()
        with make_figure() as self.figure:
            pyplot.plot(self.data)

    def _repr_html_(self):
        self.init_data()
        svg_data = get_svg(self.figure)
        serve_data = Response(content_type="image/svg+xml", body=svg_data)
        self._serve_data = serve_data
        save_these.append(serve_data)
        url = http_objects.register(serve_data)
        img = '<img src="%s" style="width: 50%%; height=auto" />' % html_quote(url)
        return img

add_global("Plot", Plot)
