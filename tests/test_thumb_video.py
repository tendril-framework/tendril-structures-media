

from tendril.config import MEDIA_VIDEO_EXTENSIONS
from tendril.utils.parsers.media.thumbnails import generate_thumbnail
from tendril.utils.parsers.media.thumbnails import generate_thumbnails


for ext in MEDIA_VIDEO_EXTENSIONS:
    fp = 'media/test' + ext
    print("### : ", ext)
    with open(fp, 'rb') as f:
        output_file = generate_thumbnail(f, output_fname=f'test{ext}.thumb_400.png', output_dir='thumbs')
    print(f"Thumbnail Generated : {output_file}")
    print('----------------------------------')


print("### : Default Sizes Generation")
fp = 'media/test.avi'
with open(fp, 'rb') as f:
    output_files = generate_thumbnails(f, output_dir='thumbs')
print(f"Thumbnails Generated : {output_files}")
