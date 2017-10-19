from PIL import Image
from PIL.ImageFile import ImageFile
from ..stdlib import FileReference, save
from tempita import html, html_quote
from ..jsonify import jsonify
from webob import Response
from urllib.parse import quote as url_quote
from io import BytesIO

save_these = []

@jsonify.register(Image.Image)
@jsonify.register(ImageFile)
def jsonify_image(x):
    from .http import http_objects
    out = BytesIO()
    x.save(out, format="png")
    serve_data = Response(content_type="image/png", body=out.getvalue())
    # This keeps it in memory, with the lifetime of the image:
    x._serve_data = serve_data
    save_these.append(serve_data)
    url = http_objects.register(serve_data)
    return {
        "type": "image",
        "url": url,
    }

class ImageReference(FileReference):
    def extra_jsonify_info(self):
        return {
            "embedded": {
                "type": "image",
                "url": "/fetch?filename=%s" % url_quote(self),
            }
        }

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

FileReference.extension_map['.png'] = ImageReference
FileReference.extension_map['.jpeg'] = ImageReference
FileReference.extension_map['.jpg'] = ImageReference
FileReference.extension_map['.gif'] = ImageReference

@save.register(Image.Image)
@save.register(ImageFile)
def save(o, path):
    o.save(path)
