

from decimal import Decimal
from typing import Optional
from pydantic.dataclasses import dataclass
from .base import MediaFileGeneralInfo


@dataclass
class AVFileGeneralInfo(MediaFileGeneralInfo):
    duration: int
    overall_bit_rate: int


@dataclass
class MediaTrackInfo(object):
    format: str
    stream_size: Optional[int]          # Missing in GIF


@dataclass
class AVTrackInfo(MediaTrackInfo):
    codec_id: Optional[str]             # Missing in Theora
    duration: int
    bit_rate: int

    def __post_init__(self):
        if isinstance(self.duration, str):
            self.duration = int(float(self.duration))  # WebM seems to return an str of float


@dataclass
class VideoTrackInfo(AVTrackInfo):
    format_profile: Optional[str]       # Missing in Theora
    format_settings: Optional[str]      # Missing in Theora
    width: int
    height: int
    bit_depth: Optional[int]            # Missing in Theora
    frame_count: int
    frame_rate: Decimal
    frame_rate_mode: Optional[str]      # Missing in Theora
    color_space: Optional[str]          # Missing in Theora
    chroma_subsampling: Optional[str]   # Missing in Theora
    bits__pixel_frame: Decimal
    writing_library: Optional[str]      # Missing in WMV
    rotation: Optional[Decimal]

    def __post_init__(self):
        super(VideoTrackInfo, self).__post_init__()
        self.frame_rate = Decimal(self.frame_rate)
        self.bits__pixel_frame = Decimal(self.bits__pixel_frame)
        if self.rotation:
            self.rotation = Decimal(self.rotation)


@dataclass
class AudioTrackInfo(AVTrackInfo):
    format_additionalfeatures: Optional[str]    # Missing in Vorbis
    muxing_mode: Optional[str]                  # Missing in multiple
    channels: int
    channel_layout: Optional[str]               # Missing in Vorbis
    sampling_rate: int
    compression_mode: Optional[str]             # Missing in WMV
    encoded_date: Optional[str]
    tagged_date: Optional[str]


@dataclass
class ImageTrackInfo(MediaTrackInfo):
    format_profile: Optional[str]
    width: int
    height: int
    bit_depth: Optional[int]
    color_space: Optional[str]
    chroma_subsampling: Optional[str]
