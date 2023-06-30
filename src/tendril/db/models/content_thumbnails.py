

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import relationship

from tendril.filestore.db.model import StoredFileModel
from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MediaContentFormatThumbnailModel(DeclBase, BaseMixin, TimestampMixin):
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("StoredFile.id"), nullable=False)
    format_id: Mapped[int] = mapped_column(ForeignKey('MediaContentFormat.id'), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

    @declared_attr
    def format(cls):
        return relationship('MediaContentFormatModel', back_populates="thumbnails", lazy="selectin")

    def export(self, full=False):
        return {f'{self.width}x{self.height}': self.stored_file.expose_uri}

    @declared_attr
    def stored_file(cls):
        return relationship(StoredFileModel, lazy="selectin")
