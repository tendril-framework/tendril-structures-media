

import os
from typing import Optional
from pypdf import PdfReader
from pydantic.dataclasses import dataclass
from .base import MediaFileInfo
from .base import MediaFileInfoParser
from .base import MediaFileGeneralInfo


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
            raise
            file.seek(0, os.SEEK_END)
            return file.tell()

    def _parse(self, file):
        rv = super(DocumentFileInfoParser, self)._parse(file)
        rv['general'] = {
            'container': "PDF",
            'file_size': self._get_size(file),
            'internet_media_type': 'application/pdf',
            'writing_application': None
        }

        reader = PdfReader(file)
        rv['document'] = self._parse_document_information(reader)
        return rv
