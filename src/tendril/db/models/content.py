

from typing import List
from typing import Optional
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin
from .content_formats import MediaContentFormatModel


class ContentModel(DeclBase, BaseMixin, TimestampMixin):
    type_name = 'generic'
    content_type = Column(String(32), nullable=False)

    bg_color = Column(String(20))

    @declared_attr
    def device_content(cls):
        return relationship("DeviceContentModel", uselist=False, back_populates='content', lazy='selectin')

    # @declared_attr
    # def advertisement(cls):
    #     return relationship("AdvertisementModel", uselist=False, back_populates='content', lazy='selectin')

    sequence_usages: Mapped[List["SequenceContentAssociationModel"]] = relationship()

    __mapper_args__ = {
        "polymorphic_identity": type_name,
        "polymorphic_on": content_type
    }

    def export(self):
        raise NotImplementedError


class MediaContentModel(ContentModel):
    type_name = 'media'
    id = Column(Integer, ForeignKey("Content.id"), primary_key=True)

    @declared_attr
    def formats(cls):
        return relationship(MediaContentFormatModel, back_populates="content", lazy="selectin")

    __mapper_args__ = {
        "polymorphic_identity": type_name
    }

    def export(self):
        raise NotImplementedError


class StructuredContentModel(ContentModel):
    type_name = 'structured'

    id = Column(Integer, ForeignKey("Content.id"), primary_key=True)
    path = Column(String(64), nullable=False)
    args = Column(mutable_json_type(dbtype=JSONB))

    __mapper_args__ = {
        "polymorphic_identity": type_name
    }

    def export(self):
        raise NotImplementedError


class SequenceContentModel(ContentModel):
    type_name = 'sequence'

    id = Column(Integer, ForeignKey("Content.id"), primary_key=True)
    default_duration = Column(Integer, nullable=False, default=10)

    contents: Mapped[List["SequenceContentAssociationModel"]] = \
        relationship(order_by="SequenceContentAssociationModel.position")

    __mapper_args__ = {
        "polymorphic_identity": type_name
    }

    def export(self):
        raise NotImplementedError


class SequenceContentAssociationModel(DeclBase):
    __tablename__ = "SequenceContentAssociation"
    sequence_id: Mapped[int] = mapped_column(ForeignKey("SequenceContent.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("Content.id"), primary_key=True)
    position: Mapped[int]
    duration: Mapped[Optional[int]]
    sequence: Mapped[SequenceContentModel] = relationship(back_populates="contents", foreign_keys=[sequence_id])
    content: Mapped[ContentModel] = relationship(back_populates="sequence_usages", foreign_keys=[content_id])
