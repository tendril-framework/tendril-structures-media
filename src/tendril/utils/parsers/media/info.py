

import os

from tendril.config import MEDIA_EXTENSIONS
from tendril.config import MEDIA_VIDEO_EXTENSIONS
from tendril.config import MEDIA_IMAGE_EXTENSIONS
from tendril.config import MEDIA_DOCUMENT_EXTENSIONS
from tendril.config import MEDIA_EXTRA_EXTENSIONS

from .base import MediaFileInfoParser
from .videos import VideoFileInfoParser
from .images import ImageFileInfoParser
from .documents import DocumentFileInfoParser


class ExtraMediaFileInfoParser(MediaFileInfoParser):
    pass


def _build_parsers():
    rv = {}
    for parser, exts in [
        (MediaFileInfoParser(), MEDIA_EXTENSIONS),
        (VideoFileInfoParser(), MEDIA_VIDEO_EXTENSIONS),
        (ImageFileInfoParser(), MEDIA_IMAGE_EXTENSIONS),
        (DocumentFileInfoParser(), MEDIA_DOCUMENT_EXTENSIONS),
        (ExtraMediaFileInfoParser(), MEDIA_EXTRA_EXTENSIONS)
    ]:
        for ext in exts:
            rv[ext] = parser
    return rv


_parsers = _build_parsers()


def get_media_info(file):
    _to_close = False
    if isinstance(file, str):
        file = open(file, 'rb')
        _to_close = True

    parser = _parsers[os.path.splitext(file.name)[1]]
    rv = parser.parse(file)

    if _to_close:
        file.close()

    return rv
