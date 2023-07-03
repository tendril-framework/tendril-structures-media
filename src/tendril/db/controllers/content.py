

from sqlalchemy.orm.exc import NoResultFound
from tendril.utils.db import with_db

from tendril.db.models.content import ContentModel
from tendril.db.models.content_formats import FileMediaContentFormatModel
from tendril.db.models.content_thumbnails import MediaContentFormatThumbnailModel
from tendril.db.controllers.interests import get_interest
from tendril.filestore.db.controller import get_stored_file
from tendril.structures.content import content_models


def _type_discriminator(type):
    if not type:
        return ContentModel
    if isinstance(type, str):
        return content_models[type]
    if issubclass(type, ContentModel):
        qmodel = type
    return qmodel


@with_db
def get_content(id=None, type=None, raise_if_none=True, session=None):
    filters = []
    qmodel = _type_discriminator(type)
    filters.append(qmodel.id == id)
    q = session.query(qmodel).filter(*filters)
    try:
        return q.one()
    except NoResultFound:
        if raise_if_none:
            raise
        return None


@with_db
def create_content(id=None, type=None, session=None, **kwargs):
    try:
        existing = get_content(id=id, session=session)
    except NoResultFound:
        pass
    else:
        raise ValueError(f"Could not create content container with "
                         f"ID {id}. Already Exists.")
    model = _type_discriminator(type)
    content = model(id=id)
    session.add(content)
    session.flush()
    return content


@with_db
def create_content_format_file(id=None, stored_file_id=None,
                               width=None, height=None, duration=None,
                               info=None, session=None):
    try:
        _ = get_content(id=id, type='media', session=session)
        format_instance = FileMediaContentFormatModel(
            stored_file_id=stored_file_id,
            content_id=id,
            width=width,
            height=height,
            duration=duration,
            info=info
        )
        session.add(format_instance)
        session.flush()
        return format_instance
    except NoResultFound:
        raise ValueError(f"Could not find a {type} content file "
                         f"container with the provided id {id}")


@with_db
def create_content_format_thumbnail(id=None, stored_file_id=None,
                                    width=None, height=None, session=None):
    try:
        thumbnail_instance = MediaContentFormatThumbnailModel(
            format_id=id,
            width=width,
            height=height,
            stored_file_id=stored_file_id
        )
        session.add(thumbnail_instance)
        session.flush()
        return thumbnail_instance
    except NoResultFound:
        raise ValueError(f"Could not find a content format "
                         f"with the provided id {id}")
