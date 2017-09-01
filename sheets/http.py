from waitress import serve
import webob
import webob.static
from webob.dec import wsgify
from weakref import WeakValueDictionary
import uuid
import os
from urllib.parse import quote as url_quote

base = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base, 'html')

static_app = webob.static.DirectoryApp(html_path, cache_control="none")

class HTTPObjects:
    def __init__(self):
        self.refs = WeakValueDictionary()

    def app(self, object_name):
        value = self.refs.get(object_name)
        if not value:
            print("Could not find object", object_name)
            return self.not_found
        return value

    @wsgify
    def not_found(self, req):
        return webob.Response(content_type="text/plain", body="Not found", status=404)

    def explicit_app(self, content_type, body):
        return webob.Response(content_type=content_type, body=body)

    def register(self, app):
        id = str(uuid.uuid1())
        self.refs[id] = app
        return "/object?name=%s" % url_quote(id)

http_objects = HTTPObjects()

@wsgify
def app(req):
    if req.path.startswith("/fetch"):
        filename = req.params.get("filename", "/does-not-exist")
        return webob.static.FileApp(filename, cache_control="none")(req)
    if req.path.startswith("/object"):
        object_name = req.params.get("name")
        return http_objects.app(object_name)
    return static_app(req)

def start(port=10100):
    serve(app, listen='127.0.0.1:%s' % port)
