

from tendril.config import MEDIA_DOCUMENT_EXTENSIONS
from tendril.utils.parsers.media.info import get_media_info


for ext in MEDIA_DOCUMENT_EXTENSIONS:
    fp = 'media/test' + ext
    print("### : ", ext)
    info = get_media_info(fp)
    print(f"Width : {info.width()}, Height: {info.height()}")
    print(info.json())
    print('----------------------------------')
