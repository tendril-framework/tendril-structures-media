

import os
import warnings
from typing import Union
from typing import Tuple
from tendril.config import MEDIA_VIDEO_EXTENSIONS
from tendril.config import MEDIA_IMAGE_EXTENSIONS
from tendril.config import MEDIA_DOCUMENT_EXTENSIONS
from tendril.config import MEDIA_THUMBNAIL_SIZES
from tendril.config import MEDIA_THUMBNAIL_BACKGROUND

from .images import ImageThumbnailGenerator
from .videos import VideoThumbnailGenerator
from .documents import DocumentThumbnailGenerator



def _build_generators():
    rv = {}
    for generator, exts in [
        (VideoThumbnailGenerator(), MEDIA_VIDEO_EXTENSIONS),
        (ImageThumbnailGenerator(), MEDIA_IMAGE_EXTENSIONS),
        (DocumentThumbnailGenerator(), MEDIA_DOCUMENT_EXTENSIONS),
    ]:
        for ext in exts:
            rv[ext] = generator
    return rv


_generators = _build_generators()


def generate_thumbnail(file, output_dir, size: Union[int, Tuple[int]] = 400, output_fname=None,
                       background=MEDIA_THUMBNAIL_BACKGROUND, output_format='png'):
    _to_close = False
    if isinstance(file, str):
        file = open(file, 'rb')
        _to_close = True

    fname, fext = os.path.splitext(os.path.split(file.name)[1])

    if not output_fname:
        if isinstance(size, int):
            output_fname = f'{fname}{fext}.thumb_{size}.{output_format}'
        else:
            output_fname = f'{fname}{fext}.thumb_{size[0]}x{size[1]}.{output_format}'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, output_fname)

    try:
        generator = _generators[fext]
    except KeyError:
        warnings.warn(f"Generator for extension {fext} not installed. "
                      f"No thumbnail will be generated.")
        return None

    if not isinstance(size, tuple):
        size = (size, size)

    outpath = generator.generate_thumbnail(file, output_path, size=size,
                                           background=background,
                                           output_format=output_format)

    if _to_close:
        file.close()

    return outpath


def generate_thumbnails(file, output_dir, background=MEDIA_THUMBNAIL_BACKGROUND):
    rv = []
    for size in MEDIA_THUMBNAIL_SIZES:
        rv.append(generate_thumbnail(file, output_dir,
                                     size=size, background=background))
    return rv
