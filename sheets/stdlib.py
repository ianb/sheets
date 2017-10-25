import os
import base64
import glob
try:
    import numpy as np
except ImportError:
    np = None
try:
    import cv2
except ImportError:
    cv2 = None
from io import BytesIO
import re
import json
from .jsonify import jsonify
from functools import singledispatch
from collections import MutableMapping
from .watcher import watch

builtin_names = ["listdir", "save", "cv_image", "watch"]

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

if cv2:
    def cv_image(an_array):
        from PIL import Image
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
        return len(list(self.__iter__()))

    def _sheets_json_(self):
        return {
            "type": "FilesDict",
            "base": os.path.abspath(self.base),
            "files": [jsonify(self[x]) for x in sorted(self)],
        }

class FileReference(str):

    extension_map = {}

    @classmethod
    def frompath(cls, f):
        ext = os.path.splitext(f)[1].lower()
        new_class = cls.extension_map.get(ext, cls)
        return new_class(f)

    def _sheets_json_(self):
        data = {
            "type": "filename",
            "filename": str(self),
            "exists": True,
        }
        if not os.path.exists(self):
            data["exists"] = False
        data.update(self.extra_jsonify_info())
        return data

    def extra_jsonify_info(self):
        return {}

    num_re = re.compile(r'\d+')

    def getnum(self):
        s = os.path.splitext(str(self))[0]
        matches = self.num_re.findall(s)
        if not matches:
            raise ValueError("File has no number: {}".format(self))
        return int(matches[-1])

class JsonReference(FileReference):

    def open(self):
        with open(self, 'r') as fp:
            return json.load(fp)

    def save(self, value):
        with open(self, 'w') as fp:
            json.dump(value, fp)

FileReference.extension_map['.json'] = JsonReference
