

import os

from typing import Union
from tendril.config import MEDIA_EXTENSIONS
from tendril.config import MEDIA_VIDEO_EXTENSIONS
from tendril.config import MEDIA_IMAGE_EXTENSIONS
from tendril.config import MEDIA_DOCUMENT_EXTENSIONS
from tendril.config import MEDIA_EXTRA_EXTENSIONS

from .base import MediaFileInfoParser
from .videos import VideoFileInfoParser
from .images import ImageFileInfoParser
from .documents import DocumentFileInfoParser

from .videos import VideoFileInfo
from .images import ImageFileInfo
from .documents import PdfFileInfo

MediaInfoTModel = Union[VideoFileInfo, ImageFileInfo, PdfFileInfo]


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


def get_media_info(file, filename=None, original_filename=None):
    _to_close = False
    if isinstance(file, str):
        filename = file
        file = open(file, 'rb')
        _to_close = True

    if not filename:
        if hasattr(file, 'filename'):
            filename = file.filename
        else:
            filename = file.name

    parser = _parsers[os.path.splitext(filename)[1]]
    rv = parser.parse(file, filename=filename,
                      original_filename=original_filename)

    if _to_close:
        file.close()

    return rv
