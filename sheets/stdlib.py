import os
import base64
import glob
try:
    from PIL import Image
    from PIL.ImageFile import ImageFile
except ImportError:
    Image = None
from io import BytesIO
from urllib.parse import quote as url_quote
from tempita import html, HTMLTemplate, html_quote
from .htmlize import htmlize
from webob import Response
from functools import singledispatch

builtin_names = ["listdir", "save"]

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

not_exists_tmpl = HTMLTemplate('''\
<code class="file" title="{{f}} does not exist"><s>{{f}}</s></code>\
''')
preview_tmpl = HTMLTemplate('''\
<code class="file" data-html="true", data-title="{{str(hover_html)}}" data-toggle="tooltip">{{f}}</code>\
''')
no_preview_tmpl = HTMLTemplate('''\
<code class="file" data-title="No preview available" data-toggle="tooltip">{{f}}</code>\
''')
