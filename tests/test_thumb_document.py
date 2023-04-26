

from tendril.config import MEDIA_DOCUMENT_EXTENSIONS
from tendril.utils.parsers.media.thumbnails import generate_thumbnail
from tendril.utils.parsers.media.thumbnails import generate_thumbnails


for ext in MEDIA_DOCUMENT_EXTENSIONS:
    fp = 'media/test' + ext
    print("### : ", ext)
    with open(fp, 'rb') as f:
        output_file = generate_thumbnail(f, output_dir='thumbs')
    print(f"Thumbnail Generated : {output_file}")
    print('----------------------------------')


print("### : Default Sizes Generation")
fp = 'media/test.pdf'
with open(fp, 'rb') as f:
    output_files = generate_thumbnails(f, output_dir='thumbs')
print(f"Thumbnails Generated : {output_files}")
