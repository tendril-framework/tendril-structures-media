

import os
from typing import Optional
from typing import Literal
from pypdf import PdfReader
from pydantic.dataclasses import dataclass
from pdf2image import convert_from_bytes
from .base import MediaFileInfo
from .base import MediaFileInfoParser
from .base import MediaFileGeneralInfo
from .base import MediaThumbnailGenerator


@dataclass
class DocumentInfo(object):
    pages: int
    author: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    subject: Optional[str]
    title: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]


@dataclass
class PdfFileInfo(MediaFileInfo):
    general: MediaFileGeneralInfo
    document: DocumentInfo

    def __post_init__(self):
        self.general = MediaFileGeneralInfo(**self.general)

    def width(self):
        return None

    def height(self):
        return None

    def duration(self):
        return -1 * self.document.pages


class DocumentFileInfoParser(MediaFileInfoParser):
    info_class = PdfFileInfo

    def _parse_document_information(self, reader):
        rv = {'pages': len(reader.pages)}
        metadata = reader.metadata
        rv['author'] = metadata.author
        rv['creator'] = metadata.creator
        rv['producer'] = metadata.producer
        rv['subject'] = metadata.subject
        rv['title'] = metadata.title
        rv['creation_date'] = metadata.creation_date_raw
        rv['modification_date'] = metadata.modification_date_raw
        return rv

    def _get_size(self, file):
        try:
            return os.fstat(file.fileno()).st_size
        except:
            file.seek(0, os.SEEK_END)
            rv = file.tell()
            file.seek(0)
            return rv

    def _parse(self, file, *args, **kwargs):
        rv = super(DocumentFileInfoParser, self)._parse(file, *args, **kwargs)
        rv['general'] = {
            'container': "PDF",
            'file_size': self._get_size(file),
            'internet_media_type': 'application/pdf',
            'writing_application': None
        }

        reader = PdfReader(file)
        rv['document'] = self._parse_document_information(reader)
        return rv


class DocumentThumbnailGenerator(MediaThumbnailGenerator):
    def generate_thumbnail(self, file, output_path, size,
                           background, output_format='png'):
        file.seek(0)
        images = convert_from_bytes(file.read(), first_page=1, last_page=1)
        file.seek(0)
        image = images[0]
        image.thumbnail(size)
        return self.pack_and_write(size, output_path, image, background)
