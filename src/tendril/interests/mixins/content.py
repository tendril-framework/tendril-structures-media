

import os
import asyncio
from asgiref.sync import async_to_sync

from httpx import HTTPStatusError

from tendril.db.controllers.interests import get_interest
from tendril.common.content.exceptions import ContentTypeMismatchError

from tendril.filestore import buckets
from tendril.config import MEDIA_UPLOAD_FILESTORE_BUCKET
from tendril.config import MEDIA_PUBLISHING_FILESTORE_BUCKET

from tendril.interests.base import InterestBase
from tendril.common.states import LifecycleStatus
from tendril.authz.roles.interests import require_state
from tendril.authz.roles.interests import require_permission

from tendril.caching import tokens
from tendril.caching.tokens import TokenStatus

from tendril.structures.content import content_types
from tendril.db.models.content import ContentModel
from tendril.db.controllers.content import create_content
from tendril.db.controllers.content import create_content_format_file
from tendril.db.controllers.content import create_content_format_thumbnail
from tendril.db.controllers.content import sequence_next_position
from tendril.db.controllers.content import sequence_heal_positions
from tendril.db.controllers.content import sequence_add_content
from tendril.db.controllers.content import sequence_remove_content
from tendril.common.content.exceptions import ContentNotReady

from tendril.utils.parsers.media.info import get_media_info
from tendril.utils.parsers.media.thumbnails import generate_thumbnails

from tendril.utils.fsutils import TEMPDIR
from tendril.utils.db import with_db
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MediaContentInterest(InterestBase):
    # WARNING.
    #
    # This is a common container for the different content types.
    # This is terrible, and needs to be fixed. The main issue is
    # the current implicit assumption of a 1-1 mapping between an
    # interest class and the model.
    #
    # Devices should have the same problem, but more effort has
    # gone into working around it there, I think.
    #
    # The resolution will probably be to extend the same kind of
    # class composition that was done at the interest level to the
    # interest class as well.

    token_namespace = 'mfu'
    upload_bucket_name = MEDIA_UPLOAD_FILESTORE_BUCKET
    publish_bucket_name = MEDIA_PUBLISHING_FILESTORE_BUCKET
    additional_creation_fields = ['content_type']
    additional_export_fields = ['content_type']

    def __init__(self, *args, content_type=None, **kwargs):
        self._content_type = content_type
        super(MediaContentInterest, self).__init__(*args, **kwargs)
        self._upload_bucket = None
        self._publish_bucket = None

    # Common
    @property
    def content_type(self):
        if not self._content_type:
            self._content_type = self._model_instance.content.content_type
        return self._content_type

    @with_db
    def set_content_type(self, content_type, session=None):
        if self._content_type and self._content_type != content_type:
            raise ValueError(f"Content Type {self._content_type} already set for interest {self.id} "
                             f"and cannot be changed. Create a new device_content instead.")
        if content_type not in content_types:
            raise ValueError(f"Content Type {content_type} is not recognized. Try one of {content_types}")
        self._content_type = content_type
        self._commit_to_db(session=session)

    @property
    def content(self):
        return self.model_instance.content

    @with_db
    def activate(self, background_tasks=None, auth_user=None, session=None):
        result, msg = super().activate(background_tasks=background_tasks,
                                       auth_user=auth_user, session=session)

        if not self.model_instance.status == LifecycleStatus.ACTIVE:
            return result, msg

        publishable = self.publishable()

        if background_tasks:
            background_tasks.add_task(self._publish_files(publishable))
        else:
            asyncio.ensure_future(self._publish_files(publishable))
        return result, msg

    async def _publish_files(self, stored_files):
        for stored_file in stored_files:
            logger.info(f"Publishing file {stored_file.filename}")
            try:
                upload_response = await self.upload_bucket.move(
                    filename=stored_file.filename,
                    target_bucket=self.publish_bucket_name,
                    actual_user=None,
                )
            except HTTPStatusError as e:
                self._report_filestore_error(None, e, "Publishing media file")
                continue

    def publishable(self):
        content = self.model_instance.content
        rv = []
        if hasattr(content, "formats"):
            for fmt in self.model_instance.content.formats:
                if hasattr(fmt, 'stored_file'):
                    if fmt.stored_file.bucket.name == self.upload_bucket_name:
                        rv.append(fmt.stored_file)
                for thumbnail in fmt.thumbnails:
                    if thumbnail.stored_file.bucket.name == self.upload_bucket_name:
                        rv.append(thumbnail.stored_file)
        return rv

    def published(self):
        if self.status != LifecycleStatus.ACTIVE:
            return False
        content = self.model_instance.content
        if hasattr(content, "formats"):
            for fmt in self.model_instance.content.formats:
                if hasattr(fmt, 'stored_file'):
                    if fmt.stored_file.bucket.name != self.publish_bucket_name:
                        return False
        return True

    @with_db
    @require_state((LifecycleStatus.ACTIVE, LifecycleStatus.APPROVAL, LifecycleStatus.NEW))
    @require_permission('read_artefacts', strip_auth=False)
    def content_information(self, full=False, auth_user=None, session=None):
        if not self._model_instance.content:
            raise ContentNotReady('read_content_info', self.id, self.name)
        else:
            content: ContentModel = self._model_instance.content
            rv = content.export(full=full)
            if full:
                if 'formats' in rv.keys():
                    for fmt_info in rv['formats']:
                        fmt_info['published'] = self.format_published(fmt_info['format_id'])
                rv['published'] = self.published()
            return rv

    @with_db
    @require_state((LifecycleStatus.ACTIVE, LifecycleStatus.APPROVAL, LifecycleStatus.NEW))
    @require_permission('read_artefacts', strip_auth=False)
    def estimated_duration(self, auth_user=None, session=None):
        return self._model_instance.content.estimated_duration()

    @with_db
    def _commit_to_db(self, must_create=False, can_create=True, session=None):
        super(MediaContentInterest, self)._commit_to_db(must_create=must_create,
                                                        can_create=can_create,
                                                        session=session)
        if not self.model_instance.content_id:
            content = create_content(type=self._content_type, session=session)
            self.model_instance.content_id = content.id
            session.add(self.model_instance)
            session.commit()
            session.flush()

    # Media Content

    @property
    def upload_bucket(self):
        if not self._upload_bucket:
            self._upload_bucket = buckets.get_bucket(self.upload_bucket_name)
        return self._upload_bucket

    @property
    def publish_bucket(self):
        if not self._publish_bucket:
            self._publish_bucket = buckets.get_bucket(self.publish_bucket_name)
        return self._publish_bucket

    @property
    def formats(self):
        return self.content.formats

    @with_db
    @require_state((LifecycleStatus.NEW))
    @require_permission('add_artefact')
    def fidx_burn(self, session=None):
        rv = self.content.fidx
        self.content.fidx += 1
        session.add(self.content)
        return rv

    def _report_filestore_error(self, token_id, e, action_comment):
        logger.warn(f"Exception while {action_comment} : HTTP {e.response.status_code} {e.response.text}")
        if token_id:
            tokens.update(
                self.token_namespace, token_id, state=TokenStatus.FAILED,
                error={"summary": f"Exception while {action_comment}",
                       "filestore": {
                           "code": e.response.status_code,
                           "content": e.response.json()}
                       }
            )

    @with_db
    @require_state((LifecycleStatus.NEW))
    @require_permission('add_artefact', strip_auth=False)
    def add_format(self, file, rename_to=None, token_id=None, auth_user=None, session=None):
        storage_folder = f'{self.id}'
        if token_id:
            tokens.update(self.token_namespace, token_id,
                          state=TokenStatus.INPROGRESS, max=6,
                          current="Parsing Media Information")

        # 1. Parse Media Information
        filename = rename_to or file.filename
        media_info = get_media_info(file.file, filename=filename, original_filename=file.filename)

        if token_id:
            tokens.update(self.token_namespace, token_id,
                          current="Uploading Media File to Filestore", done=1)

        # 2. Upload File to Bucket
        try:
            upload_response = async_to_sync(self.upload_bucket.upload)(
                file=(os.path.join(storage_folder, filename), file.file),
                actual_user=auth_user.id, interest=self.id
            )
        except HTTPStatusError as e:
            self._report_filestore_error(token_id, e, "uploading media file to bucket")
            return

        if token_id:
            tokens.update(self.token_namespace, token_id,
                          current="Generating Thumbnails", done=2)

        # 3. Generate Thumbnails

        thumbnail_folder = os.path.join(TEMPDIR, os.path.splitext(filename)[0])
        os.makedirs(thumbnail_folder, exist_ok=True)
        generated_thumbnails = generate_thumbnails(file.file, thumbnail_folder, filename=filename)

        if token_id:
            tokens.update(self.token_namespace, token_id,
                          current="Uploading Thumbnails to Filestore", done=3)

        # 4. Upload Thumbnails to Bucket

        published_thumbnails = []
        for tsize, fpath in generated_thumbnails:
            fname = os.path.split(fpath)[1]
            with open(fpath, 'rb') as thumb_file:
                try:
                    response = async_to_sync(self.upload_bucket.upload)(
                        file=(os.path.join(storage_folder, fname), thumb_file),
                        actual_user=auth_user.id, interest=self.id
                    )
                except HTTPStatusError as e:
                    self._report_filestore_error(token_id, e, "uploading thumbnail to bucket")
                    return
            published_thumbnails.append((tsize, fname, response))

        if token_id:
            tokens.update(self.token_namespace, token_id,
                          current="Registering Media Format", done=4)

        # 5. Create Format DB Entry

        format_model_instance = create_content_format_file(
            id=self.model_instance.content_id,
            stored_file_id=upload_response['storedfileid'],
            width=media_info.width(),
            height=media_info.height(),
            duration=media_info.duration(),
            info=media_info.asdict(),
        )

        if token_id:
            tokens.update(self.token_namespace, token_id,
                          current="Registering Media Format Thumbnails", done=5,
                          metadata={'format_id': format_model_instance.id})

        # 6. Create Thumbnail DB Entries

        for tsize, fname, response in published_thumbnails:
            create_content_format_thumbnail(
                id=format_model_instance.id,
                stored_file_id=response['storedfileid'],
                width=tsize[0], height=tsize[1],
            )

        if token_id:
            tokens.update(self.token_namespace, token_id, current="Finishing", done=6)

        # 7. Close Upload Ticket
        tokens.close(self.token_namespace, token_id)

    def get_format(self, format_id):
        formats = self.model_instance.content.formats
        for candidate in formats:
            if candidate.id == format_id:
                return candidate

    def format_published(self, format_id):
        fmt = self.get_format(format_id)
        if hasattr(fmt, 'stored_file'):
            if fmt.stored_file.bucket.name != self.publish_bucket_name:
                return False
        return True

    @with_db
    @require_state((LifecycleStatus.ACTIVE, LifecycleStatus.APPROVAL, LifecycleStatus.NEW))
    @require_permission('read_artefacts', strip_auth=False)
    def format_information(self, format_id, full=False, auth_user=None, session=None):
        fmt = self.get_format(format_id)
        rv = fmt.export(full=full)
        if full:
            rv['published'] = self.format_published(format_id)
        return rv

    @with_db
    @require_state((LifecycleStatus.NEW))
    @require_permission('delete_artefact', strip_auth=False)
    def delete_format(self, format_id, auth_user=None, session=None):
        pass

    # Content Providers

    @with_db
    @require_state((LifecycleStatus.NEW))
    @require_permission('add_artefact', strip_auth=False)
    def generate_from_provider(self, provider_id, args, auth_user=None, session=None):
        if self.content_type != 'structured':
            raise ContentTypeMismatchError(self.content_type, 'structured',
                                           'add_artefact', self.id, self.name)

        provider = get_interest(id=provider_id, type='content_provider', session=session).actual
        generated = provider.generate(args, auth_user=auth_user, session=session)
        for k, v in generated.items():
            setattr(self.model_instance.content, k, v)
        session.add(self.model_instance.content)
        session.flush()
        return self.model_instance.content

    # Content Sequence

    @with_db
    @require_state((LifecycleStatus.NEW, LifecycleStatus.APPROVAL, LifecycleStatus.ACTIVE))
    @require_permission('add_artefact', strip_auth=False)
    def sequence_set_default_duration(self, default_duration=10, auth_user=None, session=None):
        if self.content_type != 'sequence':
            raise ContentTypeMismatchError(self.content_type, 'sequence',
                                           'add_artefact', self.id, self.name)

        if not isinstance(default_duration, int) or default_duration < 0:
            raise ValueError("Expecting a non-negative integer for duration")

        self.model_instance.content.default_duration = default_duration
        session.add(self.model_instance.content)
        session.flush()
        return {'interest_id': self.id,
                'default_duration': self.model_instance.content.default_duration}

    @with_db
    @require_state((LifecycleStatus.NEW))
    @require_permission('add_artefact', strip_auth=False)
    def sequence_add(self, content_id, position=None, duration=None, auth_user=None, session=None):
        if self.content_type != 'sequence':
            raise ContentTypeMismatchError(self.content_type, 'sequence',
                                           'add_artefact', self.id, self.name)

        # Get Content and Verify Access
        content = get_interest(content_id, type=self.type_name, session=session).actual
        if not content.check_user_access(auth_user, 'read', session=session):
            raise PermissionError("User does not seem to have access to the underlying content. "
                                  "Cannot add to sequence.")

        if not duration:
            duration = content.estimated_duration(auth_user=auth_user, session=session)

        if not duration:
            raise ValueError("We need a duration, however none is provided and the content does "
                             "not provide it intrinsically.")

        # Create and commit Association Model
        sequence_add_content(id=self.model_instance.content_id,
                             content=content.model_instance.content_id,
                             position=position,
                             duration=duration,
                             session=session)

        sequence_heal_positions(id=self.model_instance.content_id, session=session)
        return True

    @with_db
    @require_state((LifecycleStatus.NEW))
    @require_permission('add_artefact', strip_auth=False)
    def sequence_remove(self, position=None, auth_user=None, session=None):
        if self.content_type != 'sequence':
            raise ContentTypeMismatchError(self.content_type, 'sequence',
                                           'add_artefact', self.id, self.name)

        sequence_remove_content(id=self.model_instance.content_id,
                                position=position,
                                session=session)
        sequence_heal_positions(id=self.model_instance.content_id, session=session)
        return True
