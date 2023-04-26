

import warnings
from typing import List
from typing import Optional

from pymediainfo import MediaInfo
from pymediainfo import Track

from pydantic.dataclasses import dataclass

from .base import MediaFileInfo
from .base import MediaFileInfoParser

from .av import AVFileGeneralInfo
from .av import VideoTrackInfo
from .av import AudioTrackInfo


@dataclass
class VideoFileInfo(MediaFileInfo):
    general: AVFileGeneralInfo
    video: List[VideoTrackInfo]
    audio: Optional[List[AudioTrackInfo]]

    def __post_init__(self):
        self.general = AVFileGeneralInfo(**self.general)
        self.video = [VideoTrackInfo(**x) for x in self.video]
        self.audio = [AudioTrackInfo(**x) for x in self.audio]

    def width(self):
        return self.video[0].width

    def height(self):
        return self.video[0].height


class VideoFileInfoParser(MediaFileInfoParser):
    info_class = VideoFileInfo

    def _parse_general_information(self, mi, fname=None):
        # We only really expect one general, one video, and one audio track for each
        # media file. Use cases for having more than one track, if applicable, need
        # to be individually addressed later and these warnings removed. Note that
        # we presently completely ignore other tracks. Text tracks may be useful for
        # providing subtitle localization.
        if len(mi.general_tracks) > 1:
            warnings.warn(f"Got multiple General Tracks for Video File f{fname}")

        general_track = mi.general_tracks[0]
        rv = {
            'container': general_track.format,
            'file_size': general_track.file_size,
            'duration': general_track.duration,
            'overall_bit_rate': general_track.overall_bit_rate,
            'writing_application': general_track.writing_application,
            'internet_media_type': general_track.internet_media_type
        }
        return rv

    def _parse_av_track_information(self, track: Track):
        rv = {
            'format': track.format,
            'codec_id': track.codec_id,
            'duration': track.duration,
            'bit_rate': track.bit_rate,
            'stream_size': track.stream_size,
            'encoded_date': track.encoded_date,
            'tagged_date': track.tagged_date
        }
        return rv

    def _parse_video_track_information(self, track: Track):
        rv = self._parse_av_track_information(track)
        rv['format_profile'] = track.format_profile
        rv['format_settings'] = track.format_settings
        rv['width'] = track.width
        rv['height'] = track.height
        rv['bit_depth'] = track.bit_depth
        rv['frame_count'] = track.frame_count
        rv['frame_rate'] = track.frame_rate
        rv['frame_rate_mode'] = track.frame_rate_mode
        rv['color_space'] = track.color_space
        rv['chroma_subsampling'] = track.chroma_subsampling
        rv['bits__pixel_frame'] = track.bits__pixel_frame
        rv['writing_library'] = track.writing_library
        rv['rotation'] = track.rotation
        return rv

    def _parse_video_information(self, mi, fname=None):
        if len(mi.video_tracks) > 1:
            warnings.warn(f"Got multiple Video Tracks for Video File f{fname}")
        video_track = mi.video_tracks[0]
        rv = [self._parse_video_track_information(video_track)]
        return rv

    def _parse_audio_track_information(self, track):
        rv = self._parse_av_track_information(track)
        rv['format_additionalfeatures'] = track.format_additionalfeatures
        rv['muxing_mode'] = track.muxing_mode
        rv['channels'] = track.channel_s
        rv['channel_layout'] = track.channel_layout
        rv['sampling_rate'] = track.sampling_rate
        rv['compression_mode'] = track.compression_mode
        return rv

    def _parse_audio_information(self, mi, fname=None):
        if len(mi.audio_tracks) > 1:
            warnings.warn(f"Got multiple Audio Tracks for Video File f{fname}")
        audio_track = mi.audio_tracks[0]
        rv = [self._parse_audio_track_information(audio_track)]
        return rv

    def _parse(self, file):
        rv = super(VideoFileInfoParser, self)._parse(file)
        mi = MediaInfo.parse(file, parse_speed=1.0)
        rv['general'] = self._parse_general_information(mi, fname=file.name)
        rv['video'] = self._parse_video_information(mi, fname=file.name)
        rv['audio'] = self._parse_audio_information(mi, fname=file.name)
        return rv