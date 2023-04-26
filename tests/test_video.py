

from pymediainfo import MediaInfo
from tendril.config import MEDIA_VIDEO_EXTENSIONS
from tendril.utils.parsers.media.info import get_media_info


for ext in MEDIA_VIDEO_EXTENSIONS:
    fp = 'media/test' + ext
    print("### : ", ext)
    # print(MediaInfo.parse(fp).to_data())
    info = get_media_info(fp)
    print(f"Width : {info.width()}, Height: {info.height()}")
    print(info.json())
    print('----------------------------------')
