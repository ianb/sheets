import os
import base64
import glob
try:
    import numpy as np
except ImportError:
    np = None
try:
    from PIL import Image
    from PIL.ImageFile import ImageFile
except ImportError:
    Image = None
try:
    import cv2
except ImportError:
    cv2 = None
from io import BytesIO
import re
import json
from urllib.parse import quote as url_quote
from tempita import html, HTMLTemplate, html_quote
from .htmlize import htmlize
from webob import Response
from functools import singledispatch
from collections import MutableMapping
try:
    from .matplotlibsupport import Plot
except ImportError as e:
    print("Could not import matplot support:", e)

    class Plot:
        def __init__(self, *args, **kw):
            raise NotImplementedError("You must install matplotlib")
try:
    # FIXME: re-enable
    if False:
        from . import kerassupport
        kerassupport
except ImportError as e:
    print("No Keras support:", e)

builtin_names = ["listdir", "save", "cv_image", "Plot"]

def make_data_url(content_type, content):
    return 'data:%s;base64,%s' % (content_type, base64.urlsafe_b64encode(content).decode('ascii').replace('\n', ''))

def listdir(path="."):
    paths = glob.glob(path, recursive=True)
    result = []
    for path in paths:
        if os.path.isfile(path):
            result.append(FileReference.frompath(path))
        else:
            for name in os.listdir(path):
                if path != ".":
                    name = os.path.join(path, name)
                result.append(FileReference.frompath(name))
    return sorted(result)

@singledispatch
def save(o, path):
    with open(path, 'w') as fp:
        fp.write(str(o))

if Image:
    @save.register(Image.Image)
    @save.register(ImageFile)
    def save(o, path):
        o.save(path)

if cv2 and Image:
    def cv_image(an_array):
        image = cv2.imencode(".png", an_array)[1].tostring()
        input = BytesIO(image)
        return Image.open(input)
else:
    def cv_image(an_array):
        raise NotImplementedError("Libraries not installed")

class FilesDict(MutableMapping):
    def __init__(self, base="."):
        self.base = base

    def _fullpath(self, path):
        path = os.path.join(self.base, path)
        if not os.path.abspath(path).startswith(os.path.abspath(self.base)):
            raise ValueError(
                "Bad path {}, not under {}"
                % (os.path.abspath(path), os.path.abspath(self.base)))
        if path.startswith("./"):
            path = path[2:]
        return path

    def __getitem__(self, path):
        path = self._fullpath(path)
        if not os.path.exists(path):
            raise KeyError
        return FileReference.frompath(path)

    def __setitem__(self, path, value):
        path = self._fullpath(path)
        pathobj = FileReference.frompath(path)
        if hasattr(pathobj, "save"):
            pathobj.save(value)
        else:
            save(value, path)

    def __delitem__(self, path):
        path = self._fullpath(path)
        if not os.path.exists(path):
            raise KeyError("No such file: {}".format(path))
        # FIXME: have some way to undo:
        # os.unlink(path)

    def __iter__(self):
        for filename in os.listdir(self.base):
            full = self._fullpath(filename)
            if os.path.isdir(full):
                continue
            yield filename

    def __len__(self):
        return len(list(self))

class FileReference(str):

    extension_map = {}

    @classmethod
    def frompath(cls, f):
        ext = os.path.splitext(f)[1].lower()
        new_class = cls.extension_map.get(ext, cls)
        return new_class(f)

    def _repr_html_(self):
        if not os.path.exists(self):
            return html(not_exists_tmpl.substitute(f=self))
        return html(no_preview_tmpl.substitute(f=self))

    num_re = re.compile(r'\d+')

    def getnum(self):
        s = os.path.splitext(str(self))[0]
        matches = self.num_re.findall(s)
        if not matches:
            raise ValueError("File has no number: {}".format(self))
        return int(matches[-1])

class ImageReference(FileReference):
    def _repr_html_(self):
        preview = '<img src="/fetch?filename=%s" style="width: 180px; height: auto"/>' % (
            url_quote(self))
        return preview_tmpl.substitute(f=self, hover_html=preview)

    def open(self):
        if Image:
            im = Image.open(self)
            # This avoids running out of files: https://github.com/python-pillow/Pillow/issues/1237
            try:
                return im.copy()
            finally:
                im.close()
        else:
            raise NotImplementedError("You must  pip install pillow")

    def opencv(self):
        if cv2:
            return cv2.imread(self)
        else:
            raise NotImplementedError("You must  pip install opencv-python")

if Image:
    # FIXME: weakref doesn't work like we'd want it to...
    save_these = []

    @htmlize.register(Image.Image)
    @htmlize.register(ImageFile)
    def htmlize_image(x):
        from .http import http_objects
        out = BytesIO()
        x.save(out, format="png")
        serve_data = Response(content_type="image/png", body=out.getvalue())
        # This keeps it in memory, with the lifetime of the image:
        x._serve_data = serve_data
        save_these.append(serve_data)
        url = http_objects.register(serve_data)
        img = '<img src="%s" style="width: 180px; height=auto" />' % html_quote(url)
        return html(preview_tmpl.substitute(f=repr(x), hover_html=img))

FileReference.extension_map['.png'] = ImageReference
FileReference.extension_map['.jpeg'] = ImageReference
FileReference.extension_map['.jpg'] = ImageReference
FileReference.extension_map['.gif'] = ImageReference

class JsonReference(FileReference):

    def open(self):
        with open(self, 'r') as fp:
            return json.load(fp)

    def save(self, value):
        with open(self, 'w') as fp:
            json.dump(value, fp)

FileReference.extension_map['.json'] = JsonReference


not_exists_tmpl = HTMLTemplate('''\
<code class="file" title="{{f}} does not exist"><s>{{f}}</s></code>\
''')
preview_tmpl = HTMLTemplate('''\
<code class="file" data-html="true", data-title="{{str(hover_html)}}" data-toggle="tooltip">{{f}}</code>\
''')
no_preview_tmpl = HTMLTemplate('''\
<code class="file" data-title="No preview available" data-toggle="tooltip">{{f}}</code>\
''')
