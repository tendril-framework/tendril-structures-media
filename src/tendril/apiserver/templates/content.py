

import os
from typing import Dict
from typing import Union
from typing import Optional
from pydantic.fields import Field

from fastapi import APIRouter
from fastapi import Request
from fastapi import Depends
from fastapi import File
from fastapi import Body
from fastapi import UploadFile
from fastapi import BackgroundTasks

from tendril.authn.users import auth_spec
from tendril.authn.users import AuthUserModel
from tendril.authn.users import authn_dependency

from tendril.apiserver.templates.base import ApiRouterGenerator
from tendril.utils.pydantic import TendrilTORMModel
from tendril.utils.pydantic import TendrilTBaseModel
from tendril.utils.db import get_session

from tendril.caching import tokens
from tendril.caching.tokens import GenericTokenTModel

from tendril.structures.content import content_models
from tendril.config import MEDIA_EXTENSIONS
from tendril.interests.mixins.content import MediaContentInterest
from tendril.common.content.exceptions import ContentTypeMismatchError
from tendril.common.content.exceptions import FileTypeUnsupported
from tendril.db.models.content_formats import MediaContentFormatInfoTModel
from tendril.db.models.content_formats import MediaContentFormatInfoFullTModel
from tendril.db.models.content import MediaContentInfoTModel
from tendril.db.models.content import MediaContentInfoFullTModel


class ContentTypeDetailTModel(TendrilTORMModel):
    type_description: str = Field(..., alias='display_name')


class SequenceDefaultDurationResponseTModel(TendrilTBaseModel):
    interest_id: int
    default_duration: int


class SequenceAddTModel(TendrilTBaseModel):
    content_id: int
    position: Optional[int]
    duration: Optional[int]


class InterestContentRouterGenerator(ApiRouterGenerator):
    def __init__(self, actual):
        super(InterestContentRouterGenerator, self).__init__()
        self._actual = actual

    async def accepted_types(self, request: Request,
                             user: AuthUserModel = auth_spec()):
        return self._actual.accepted_types

    async def content_info(self, request: Request,
                           id: int, full: bool = False,
                           user: AuthUserModel = auth_spec()):
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            return interest.content_information(full=full, auth_user=user, session=session)

    async def upload_media_format(self, request: Request,
                                  id: int, background_tasks: BackgroundTasks,
                                  file: UploadFile = File(...),
                                  user: AuthUserModel = auth_spec()):
        """
        Warning : This can only be done when the interest is in the NEW state. This
                  enforces approval requirements on any change in the formats. An additional
                  API endpoint (something like reset approvals?) is needed for this.
        """
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)

            # Make sure it's the correct content type before doing anything.
            if not content_models[interest.content_type].allows_actual_media:
                raise ContentTypeMismatchError(interest.content_type, 'media',
                                               'add_artefact', interest.id, interest.name,)

            # Ensure we accept the file extension
            file_ext = os.path.splitext(file.filename)[1]
            if file_ext not in MEDIA_EXTENSIONS:
                raise FileTypeUnsupported(file_ext, MEDIA_EXTENSIONS,
                                          'add_artefact', interest.id, interest.name,)

            # Get Auth clearance before sending the task to the background. This will
            # raise an exception if there is a problem.
            interest.add_format(probe_only=True, auth_user=user, session=session)

            # Burn an fidx and lock in the filename for the uploaded file.
            fidx = interest.fidx_burn(auth_user=user, session=session)
            storage_filename = f"{interest.name}_f{fidx}{file_ext}"

            # The above prechecks are required at the API level here since we are delegating
            # to a background task, and we want to avoid forcing the client to deal with
            # exceptions in that context.

            # TODO Consider providing a helper function in the interest iteself to do
            #  this stuff instead. The interest otherwise remains bare and unprotected.

            # Generate Upload Ticket and return
            upload_token = tokens.open(
                namespace='mfu',
                metadata={'interest_id': interest.id,
                          'filename': storage_filename},
                user=user.id, current="Request Created",
                progress_max=1, ttl=600,
            )

            background_tasks.add_task(interest.add_format, file=file,
                                      rename_to=storage_filename,
                                      token_id=upload_token.id,
                                      auth_user=user, session=session)

        return upload_token

    async def format_info(self, request: Request, id: int, format_id: int,
                          full: bool = True,
                          user: AuthUserModel = auth_spec()):
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            return interest.format_information(format_id, full=full, auth_user=user, session=session)

    async def delete_media_format(self, request: Request,
                                  id: int, filename: str,
                                  user: AuthUserModel = auth_spec()):
        """
        Warning : This can only be done when the interest is in the NEW state. This
                  enforces approval requirements on any change in the formats. An additional
                  API endpoint (something like reset approvals?) is needed for this.
        """
        pass

    async def generate_provider_content(self, request:Request, id:int,
                                        provider_id:int, args: dict=Body(...),
                                        user: AuthUserModel = auth_spec()):
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            return interest.generate_from_provider(provider_id, args=args, auth_user=user, session=session)

    async def set_sequence_default_duration(self, request:Request, id:int,
                                            duration:int = 10000,
                                            user: AuthUserModel = auth_spec()):
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            return interest.sequence_set_default_duration(default_duration=duration, auth_user=user, session=session)

    async def add_to_sequence(self, request:Request, id:int, item: SequenceAddTModel,
                              full=True, user: AuthUserModel = auth_spec()):
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            result = interest.sequence_add(**item.dict(), auth_user=user, session=session)

        if not result:
            raise Exception

        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            return interest.content_information(full=full, auth_user=user, session=session)

    async def remove_from_sequence(self, request:Request, id:int, position:int,
                                   full=True, user: AuthUserModel = auth_spec()):
        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            result = interest.sequence_remove(position=position, auth_user=user, session=session)

        if not result:
            raise Exception

        with get_session() as session:
            interest: MediaContentInterest = self._actual.item(id=id, session=session)
            return interest.content_information(full=full, auth_user=user, session=session)

    async def change_item_duration(self, request:Request, id:int,
                                   position:int, duration:int,
                                   user: AuthUserModel = auth_spec()):
        pass

    def generate(self, name):
        desc = f'Content API for {name} Interests'
        prefix = self._actual.interest_class.model.role_spec.prefix
        router = APIRouter(prefix=f'/{name}', tags=[desc],
                           dependencies=[Depends(authn_dependency)])

        router.add_api_route("/allowed_types", self.accepted_types, methods=["GET"],
                             response_model=Dict[str, ContentTypeDetailTModel],
                             response_model_exclude_none=True,
                             dependencies=[auth_spec(scopes=[f'{prefix}:read'])], )

        router.add_api_route("/{id}/content_info", self.content_info, methods=["GET"],
                             response_model=Union[MediaContentInfoFullTModel, MediaContentInfoTModel],
                             response_model_exclude_none=True,
                             dependencies=[auth_spec(scopes=[f'{prefix}:read'])])

        if 'media' in self._actual.accepted_types.keys():
            router.add_api_route("/{id}/formats/info/{format_id}", self.format_info, methods=["GET"],
                                 response_model=Union[MediaContentFormatInfoFullTModel, MediaContentFormatInfoTModel],
                                 response_model_exclude_none=True,
                                 dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

            router.add_api_route("/{id}/formats/upload", self.upload_media_format, methods=["POST"],
                                 response_model=GenericTokenTModel,
                                 dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

            # router.add_api_route("/{id}/formats/delete", self.delete_media_format, methods=["POST"],
            #                      # response_model=[],
            #                      dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

        if 'structured' in self._actual.accepted_types.keys():
            router.add_api_route("/{id}/provider/{provider_id}/generate", self.generate_provider_content, methods=['POST'],
                                 # response_model=,
                                 dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

        if 'sequence' in self._actual.accepted_types.keys():
            router.add_api_route("/{id}/sequence/duration", self.set_sequence_default_duration, methods=['POST'],
                                 response_model=SequenceDefaultDurationResponseTModel,
                                 dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

            router.add_api_route("/{id}/sequence/add", self.add_to_sequence, methods=['POST'],
                                 # response_model=,
                                 dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

            router.add_api_route("/{id}/sequence/remove/{position}", self.remove_from_sequence, methods=['POST'],
                                 # response_model=,
                                 dependencies=[auth_spec(scopes=[f'{prefix}:write'])])

        return [router]
