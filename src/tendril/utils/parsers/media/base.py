

import os
import json
from typing import Optional
from pydantic.dataclasses import dataclass
from dataclasses import asdict
from pydantic.json import pydantic_encoder

from PIL import Image


@dataclass
class MediaFileGeneralInfo(object):
    container: str
    file_size: int
    writing_application: Optional[str]
    internet_media_type: str            # Missing in WebP


def _strip_nones(nested_dict: dict):
    for k in list(nested_dict.keys()):
        v = nested_dict[k]
        if v is None:
            nested_dict.pop(k)
        if isinstance(v, dict):
            nested_dict[k] = _strip_nones(v)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _strip_nones(item)
    return nested_dict


@dataclass
class MediaFileInfo(object):
    filename: str
    original_filename: str
    ext: str

    def asdict(self):
        return _strip_nones(asdict(self))

    def json(self):
        return json.dumps(self.asdict(), indent=2,
                          default=pydantic_encoder)

    def width(self):
        raise NotImplementedError

    def height(self):
        raise NotImplementedError

    def duration(self):
        raise NotImplementedError


class MediaFileInfoParser(object):
    info_class = MediaFileInfo

    def _get_filename(self, file):
        if isinstance(file, str):
            return file
        elif hasattr(file, 'name'):
            return file.name
        elif hasattr(file, 'filename'):
            return file.filename

    def _parse(self, file, filename=None, original_filename=None):
        if not filename:
            filename = self._get_filename(file)
        rv = {'filename': os.path.split(filename)[-1],
              'original_filename': original_filename,
              'ext': os.path.splitext(filename)[1]}
        return rv

    def parse(self, file, *args, **kwargs):
        return self.info_class(**self._parse(file, *args, **kwargs))


class MediaThumbnailGenerator(object):
    def pack_and_write(self, size, output_path, image, background):
        if background:
            if len(background) == 4 and background[3] < 255:
                canvas_format = 'RGBA'
            else:
                canvas_format = 'RGB'
            canvas = Image.new(canvas_format, size, background)
            canvas.paste(image,
                         (int((size[0] - image.size[0]) / 2),
                          int((size[1] - image.size[1]) / 2)))
            canvas.save(output_path, optimize=True, progressive=True, quality=75)
        else:
            image.convert('RGB').save(output_path, optimize=True, progressive=True, quality=75)
        return output_path

    def generate_thumbnail(self, file, output_path, size, background,
                           output_format='png'):
        raise NotImplementedError
