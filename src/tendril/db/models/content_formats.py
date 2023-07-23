

from typing import Any
from typing import Dict
from typing import Optional
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy_json import mutable_json_type
from sqlalchemy.dialects.postgresql import JSONB

from tendril.filestore.db.model import StoredFileModel
from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin
from tendril.utils.pydantic import TendrilTBaseModel

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class StoredFileHashTModel(TendrilTBaseModel):
    sha256: Optional[str]

class MediaContentFormatInfoTModel(TendrilTBaseModel):
    format_class: str
    format_id: int
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    uri: str
    hash: StoredFileHashTModel
    published: Optional[bool]


ThumbnailListingTModel = Dict[str, str]


class MediaContentFormatInfoFullTModel(MediaContentFormatInfoTModel):
    info: Any
    thumbnails: ThumbnailListingTModel


class MediaContentFormatModel(DeclBase, BaseMixin, TimestampMixin):
    format_class_name = 'generic'
    format_class = Column(String(32), nullable=False)

    content_id: Mapped[int] = mapped_column(ForeignKey('MediaContent.id'))
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    info = Column(mutable_json_type(dbtype=JSONB, nested=True), default={})

    @declared_attr
    def content(cls):
        return relationship('MediaContentModel',
                            back_populates="formats", lazy="selectin")

    @declared_attr
    def thumbnails(cls):
        return relationship('MediaContentFormatThumbnailModel',
                            back_populates='format', lazy='selectin')

    def export_thumbnails(self):
        rv = {}
        for t in self.thumbnails:
            rv.update(t.export())
        return rv

    def export(self, full=False):
        rv = {'format_class': self.format_class_name,
              'format_id': self.id,
              'duration': self.duration}
        if self.width or self.height:
            rv['width'] = self.width
            rv['height'] = self.height
            if full:
                rv['info'] = self.info
        if full:
            rv['thumbnails'] = self.export_thumbnails()
        return rv

    def estimated_duration(self):
        if self.duration:
            if self.duration < 0:
                return self.duration * -10000
            return self.duration
        else:
            return 10000

    __mapper_args__ = {
        "polymorphic_identity": format_class_name,
        "polymorphic_on": format_class
    }


class ExternalPublishedMediaContentFormatModel(MediaContentFormatModel):
    format_class_name = 'external_published'
    id = Column(Integer, ForeignKey("MediaContentFormat.id"), primary_key=True)
    uri = Column(String, nullable=False)

    def export(self, full=False):
        rv = super(ExternalPublishedMediaContentFormatModel, self).export(full=full)
        rv['uri'] = self.uri
        return rv

    __mapper_args__ = {
        "polymorphic_identity": format_class_name,
    }


class FileMediaContentFormatModel(MediaContentFormatModel):
    format_class_name = 'file_media'
    id = Column(Integer, ForeignKey("MediaContentFormat.id"), primary_key=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("StoredFile.id"), nullable=False)

    @declared_attr
    def stored_file(cls):
        return relationship(StoredFileModel, lazy="selectin")

    def export(self, full=False):
        rv = super(FileMediaContentFormatModel, self).export(full=full)
        rv['uri'] = self.stored_file.expose_uri
        rv['hash'] = self.stored_file.fileinfo['hash']
        return rv

    __mapper_args__ = {
        "polymorphic_identity": format_class_name,
    }
