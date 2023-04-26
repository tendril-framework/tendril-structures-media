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
        "[400]",
        "List of thumbnail sizes to generate for media content. If integers are provided, "
        "thumbnails will be square with MEDIA_THUMBNAIL_BACKGROUND in the remaining area. "
        "If a different shape is desired, provide tuples of two elements. Integers and "
        "tuples can be mixed."
    ),
    ConfigOption(
        'MEDIA_THUMBNAIL_BACKGROUND',
        "(255,255,255,0)",
        "Background color to use for thumbnails. The default leaves a completely empty "
        "alpha channel"
    )
]


def load(manager):
    logger.debug("Loading {0}".format(__name__))
    manager.load_elements(config_elements_media,
                          doc="Media Content Configuration")
