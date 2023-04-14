

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


class MediaContentFormatModel(DeclBase, BaseMixin, TimestampMixin):
    format_class_name = 'generic'
    format_class = Column(String(32), nullable=False)

    content_id: Mapped[int] = mapped_column(ForeignKey('MediaContent.id'))
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    info = Column(mutable_json_type(dbtype=JSONB), default={})

    @declared_attr
    def content(cls):
        return relationship('MediaContentModel', back_populates="formats", lazy="selectin")

    __mapper_args__ = {
        "polymorphic_identity": format_class_name,
        "polymorphic_on": format_class
    }


class ExternalPublishedMediaContentFormatModel(MediaContentFormatModel):
    format_class_name = 'external_published'
    id = Column(Integer, ForeignKey("MediaContentFormat.id"), primary_key=True)
    uri = Column(String, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": format_class_name,
    }


class FileMediaContentFormatModel(MediaContentFormatModel):
    format_class_name = 'file_media'
    id = Column(Integer, ForeignKey("MediaContentFormat.id"), primary_key=True)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("StoredFile.id"))

    @declared_attr
    def stored_file(cls):
        return relationship(StoredFileModel, lazy="selectin")

    __mapper_args__ = {
        "polymorphic_identity": format_class_name,
    }
