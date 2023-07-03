

from typing import Any
from typing import List
from typing import Union
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
from tendril.utils.pydantic import TendrilTBaseModel
from .content_formats import MediaContentFormatModel
from .content_formats import ThumbnailListingTModel
from .content_formats import MediaContentFormatInfoTModel
from .content_formats import MediaContentFormatInfoFullTModel

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MediaContentInfoTModel(TendrilTBaseModel):
    # TODO Split this into a union of types
    content_type: str
    bg_color: Optional[Any]
    path: Optional[str]
    args: Optional[dict]
    formats: List[Union[MediaContentFormatInfoFullTModel,
                        MediaContentFormatInfoTModel]] = []
    thumbnails: Optional[ThumbnailListingTModel]


class MediaContentInfoFullTModel(MediaContentInfoTModel):
    published: bool


class ContentModel(DeclBase, BaseMixin, TimestampMixin):
    type_name = 'generic'
    type_description = "Other"
    content_type = Column(String(32), nullable=False, default=type_name)
    allows_actual_media = False

    bg_color = Column(String(20))

    @declared_attr
    def device_content(cls):
        return relationship("DeviceContentModel", uselist=False, back_populates='content', lazy='select')

    @declared_attr
    def advertisement(cls):
        return relationship("AdvertisementModel", uselist=False, back_populates='content', lazy='select')

    sequence_usages: Mapped[List["SequenceContentAssociationModel"]] = relationship()

    __mapper_args__ = {
        "polymorphic_identity": type_name,
        "polymorphic_on": content_type
    }

    def export(self, full=False):
        rv = {'content_type': self.content_type}
        if self.bg_color:
            rv['bg_color'] = self.bg_color
        return rv

    def estimated_duration(self):
        return None


class MediaContentModel(ContentModel):
    type_name = 'media'
    type_description = "Single Media File"
    id = Column(Integer, ForeignKey("Content.id"), primary_key=True)
    allows_actual_media = True
    fidx = Column(Integer, default=0, nullable=False)

    @declared_attr
    def formats(cls):
        return relationship(MediaContentFormatModel, back_populates="content", lazy="selectin")

    __mapper_args__ = {
        "polymorphic_identity": type_name
    }

    def export(self, full=False):
        rv = super(MediaContentModel, self).export(full=full)
        rv['formats'] = [x.export(full=full) for x in self.formats]
        for fmt in self.formats:
            if len(fmt.thumbnails):
                rv['thumbnails'] = fmt.export_thumbnails()
                break
        return rv

    def estimated_duration(self):
        return max([x.estimated_duration for x in self.formats])


class StructuredContentModel(ContentModel):
    type_name = 'structured'
    type_description = "Device Assembled Structured Content"

    id = Column(Integer, ForeignKey("Content.id"), primary_key=True)
    path = Column(String(64))
    args = Column(mutable_json_type(dbtype=JSONB))

    __mapper_args__ = {
        "polymorphic_identity": type_name
    }

    def export(self, full=False):
        rv = super(StructuredContentModel, self).export(full=full)
        rv['path'] = self.path
        if self.args:
            rv['args'] = self.args
        return rv

    def estimated_duration(self):
        return None


class SequenceContentModel(ContentModel):
    type_name = 'sequence'
    type_description = "Sequence of other content types"

    id = Column(Integer, ForeignKey("Content.id"), primary_key=True)
    default_duration = Column(Integer, nullable=False, default=10)

    contents: Mapped[List["SequenceContentAssociationModel"]] = \
        relationship(order_by="SequenceContentAssociationModel.position")

    __mapper_args__ = {
        "polymorphic_identity": type_name
    }

    def export(self, full=False):
        rv = super(SequenceContentModel, self).export(full=full)
        rv['default_duration'] = self.default_duration
        rv['contents'] = [x.export(full=full) for x in self.contents]
        return rv

    def estimated_duration(self):
        contents = self.contents
        return sum([x.estimated_duration() or self.default_duration
                    for x in contents]) + len(contents)


class SequenceContentAssociationModel(DeclBase):
    __tablename__ = "SequenceContentAssociation"
    sequence_id: Mapped[int] = mapped_column(ForeignKey("SequenceContent.id"), primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("Content.id"), primary_key=True)
    position: Mapped[int]
    duration: Mapped[Optional[int]]
    sequence: Mapped[SequenceContentModel] = relationship(back_populates="contents", foreign_keys=[sequence_id])
    content: Mapped[ContentModel] = relationship(back_populates="sequence_usages", foreign_keys=[content_id])
