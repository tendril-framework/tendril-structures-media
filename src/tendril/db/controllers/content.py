

from sqlalchemy.orm.exc import NoResultFound
from tendril.utils.db import with_db

from tendril.db.models.content import ContentModel
from tendril.db.models.content_formats import FileMediaContentFormatModel
from tendril.db.models.content_thumbnails import MediaContentFormatThumbnailModel
from tendril.db.models.content import SequenceContentAssociationModel
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

@with_db
def sequence_next_position(id=None, session=None):
    try:
        sequence = get_content(id=id, type='sequence', session=session)
        return max([x.position for x in sequence.contents], default=-1) + 1
    except NoResultFound:
        raise ValueError(f"Could not find a 'sequence' content "
                         f"container with the provided id {id}")


@with_db
def sequence_get_at_position(id, position, session=None):
    try:
        sequence = get_content(id=id, type='sequence', session=session)
        for x in sequence.contents:
            if x.position == position:
                return x
    except NoResultFound:
        raise ValueError(f"Could not find a 'sequence' content "
                         f"container with the provided id {id}")


@with_db
def sequence_prep_position(id, position, session=None):
    existing = sequence_get_at_position(id, position, session=session)
    if not existing:
        return
    sequence_prep_position(id, position + 1, session=session)
    existing.position = position + 1
    session.flush()

@with_db
def sequence_add_content(id, content, position=None, duration=None, session=None):
    content_id = content
    if position is None:
        position = sequence_next_position(id=id, session=session)
    else:
        sequence_prep_position(id, position, session=session)
    if not content_id:
        raise ValueError(f"Don't have a valid content_id. Got {content}")
    association = SequenceContentAssociationModel(sequence_id=id,
                                                  content_id=content_id,
                                                  position=position,
                                                  duration=duration)
    session.add(association)
    session.commit()


@with_db
def sequence_remove_content(id, position, session=None):
    assn = sequence_get_at_position(id=id, position=position, session=session)
    if not assn:
        raise ValueError(f"Sequence does not seem to have any "
                         f"content at position {position}.")
    session.delete(assn)
    session.commit()


@with_db
def sequence_pull_back_position(id, position, to_position, session=None):
    assn = sequence_get_at_position(id=id, position=position, session=session)
    if not assn:
        sequence_pull_back_position(id, position + 1, to_position, session=session)
    else:
        assn.position = to_position
        session.commit()


@with_db
def sequence_heal_positions(id=None, session=None):
    try:
        sequence = get_content(id=id, type='sequence', session=session)
        session.expire(sequence)
        if not len(sequence.contents):
            return
        for position in range(len(sequence.contents)):
            if not sequence_get_at_position(id=id, position=position, session=session):
                sequence_pull_back_position(id=id, position=position + 1, to_position=position, session=session)
    except NoResultFound:
        raise ValueError(f"Could not find a 'sequence' content "
                         f"container with the provided id {id}")
