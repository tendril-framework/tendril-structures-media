

import warnings
from PIL import Image
from typing import List
from typing import Literal
from pydantic.dataclasses import dataclass
from pymediainfo import MediaInfo
from pymediainfo import Track

from .av import ImageTrackInfo
from .base import MediaFileGeneralInfo
from .base import MediaFileInfo
from .base import MediaFileInfoParser
from .base import MediaThumbnailGenerator


@dataclass
class ImageFileInfo(MediaFileInfo):
    general: MediaFileGeneralInfo
    image: List[ImageTrackInfo]

    def __post_init__(self):
        self.general = MediaFileGeneralInfo(**self.general)
        self.image = [ImageTrackInfo(**x) for x in self.image]

    def width(self):
        return self.image[0].width

    def height(self):
        return self.image[0].height

    def duration(self):
        return -1


class ImageFileInfoParser(MediaFileInfoParser):
    info_class = ImageFileInfo

    def _parse_general_information(self, mi, fname=None):
        # We only really expect one general, one image track for each
        # media file. Use cases for having more than one track, if applicable, need
        # to be individually addressed later and these warnings removed. Note that
        # we presently completely ignore other tracks.
        if len(mi.general_tracks) > 1:
            warnings.warn(f"Got multiple General Tracks for Image File f{fname}")

        general_track = mi.general_tracks[0]
        rv = {
            'container': general_track.format,
            'file_size': general_track.file_size,
            'writing_application': general_track.writing_application,
            'internet_media_type': general_track.internet_media_type
        }
        return rv

    def _parse_media_track_information(self, track: Track):
        rv = {
            'format': track.format,
            'stream_size': track.stream_size,
            'encoded_date': track.encoded_date,
            'tagged_date': track.tagged_date
        }
        return rv

    def _parse_image_track_information(self, track):
        rv = self._parse_media_track_information(track)
        rv['format_profile'] = track.format_profile
        rv['width'] = track.width
        rv['height'] = track.height
        rv['bit_depth'] = track.bit_depth
        rv['color_space'] = track.color_space
        rv['chroma_subsampling'] = track.chroma_subsampling
        return rv

    def _parse_image_information(self, mi, fname=None):
        if len(mi.image_tracks) > 1:
            warnings.warn(f"Got multiple Image Tracks for Image File f{fname}")
        image_track = mi.image_tracks[0]
        rv = [self._parse_image_track_information(image_track)]
        return rv

    def _parse(self, file, *args, **kwargs):
        ofname = kwargs.get('original_filename') or kwargs.get('filename')
        rv = super(ImageFileInfoParser, self)._parse(file, *args, **kwargs)
        mi = MediaInfo.parse(file)
        rv['general'] = self._parse_general_information(mi, fname=ofname)
        rv['image'] = self._parse_image_information(mi, fname=ofname)
        return rv


class ImageThumbnailGenerator(MediaThumbnailGenerator):
    def generate_thumbnail(self, file, output_path, size,
                           background, output_format='png'):
        image = Image.open(file)
        image.thumbnail(size)
        return self.pack_and_write(size, output_path, image, background)
