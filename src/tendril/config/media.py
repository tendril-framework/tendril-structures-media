# Copyright (C) 2019 Chintalagiri Shashank
#
# This file is part of Tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Media Content Configuration Options
====================================
"""


from tendril.utils.config import ConfigOption
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

depends = ['tendril.config.core']

config_elements_media = [
    ConfigOption(
        'MEDIA_VIDEO_EXTENSIONS',
        "['.avi', '.mov', '.mp4', '.ogv', '.webm', '.wmv']",
        "List of recognized extensions for video files."
    ),
    ConfigOption(
        'MEDIA_IMAGE_EXTENSIONS',
        "['.jpg', '.png', '.gif']",           # WebP, SVG, Tiff don't play well with MediaInfo
        "List of recognized extensions for video files."
    ),
    ConfigOption(
        'MEDIA_DOCUMENT_EXTENSIONS',
        "['.pdf']",
        "List of recognized extensions for document files."
    ),
    ConfigOption(
        'MEDIA_EXTRA_EXTENSIONS',
        "[]",
        "List of extra extensions to recognize as media files. Note "
        "that this is only provided for highly specialized cases and "
        "for development-time use. Extensions listed here will "
        "probably break other code in unpredictable ways if used."
    ),
    ConfigOption(
        'MEDIA_EXTENSIONS',
        "MEDIA_VIDEO_EXTENSIONS + MEDIA_IMAGE_EXTENSIONS + MEDIA_DOCUMENT_EXTENSIONS + MEDIA_EXTRA_EXTENSIONS",
        "List of recognized extensions for media files"
    ),
    ConfigOption(
        'MEDIA_THUMBNAIL_SIZES',
        "[128,256,512]",
        "List of thumbnail sizes to generate for media content. If integers are provided, "
        "thumbnails will be square with MEDIA_THUMBNAIL_BACKGROUND in the remaining area. "
        "If a different shape is desired, provide tuples of two elements. Integers and "
        "tuples can be mixed."
    ),
    ConfigOption(
        'MEDIA_THUMBNAIL_BACKGROUND',
        "None",
        "If the thumbnail is to be paaded, then the background color to use for thumbnails. "
        "Leave as None to disable thumbnail padding. In principle, padding is "
        "relatively inexpensive and can provide well-sized images. However, if the "
        "background color uses an alpha channel, thumbnails will be generated in PNG and "
        "will be about 10 times larger, so use only if bandwidth is not a concern at all "
        "and latency is very low - essentially only for LAN deployments."
        "(255,255,255) creates a letterbox effect with a white background. Provide RGBA "
        "colors such as (255,255,255, 0) instead if transparency is needed. "
    ),
    ConfigOption(
        'MEDIA_UPLOAD_FILESTORE_BUCKET',
        '"incoming"',
        "The filestore bucket in which to write uploaded media files. Note that filestore "
        "will not have this bucket by default. You must create it or choose one that exists."
    ),
    ConfigOption(
        'MEDIA_PUBLISHING_FILESTORE_BUCKET',
        '"cdn"',
        "The filestore bucket in which published media files are to be written Note that "
        "filestore will not have this bucket by default. You must create it or choose one "
        "that exists."
    )
]


def load(manager):
    logger.debug("Loading {0}".format(__name__))
    manager.load_elements(config_elements_media,
                          doc="Media Content Configuration")
