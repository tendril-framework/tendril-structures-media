

from sqlalchemy.exc import NoResultFound
from tendril.db.controllers.interests import get_interest

from tendril.utils.db import with_db
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class ContentProviderBase(object):
    name = 'base'
    display_name = 'Base Content Provider'
    interest_class = None
    path = None
    args = {}
    requires_app = None

    def __init__(self):
        self._interest = None

    @with_db
    def commit_to_db(self, session=None):
        try:
            self._interest = get_interest(name=self.name,
                                          type=self.interest_class,
                                          session=session)
            # TODO Implement update here.
            #  Right now these things are purely write-only.
        except NoResultFound:
            self._interest = self.interest_class(name=self.name,
                                                 path=self.path, iargs=self.args,
                                                 requires_app=self.requires_app,
                                                 must_create=True, session=session)
            self._interest.set_descriptive_name(self.display_name, session=session)
            self._auto_activate(session=session)

    @with_db
    def _auto_activate(self, session=None):
        session.flush()
        from tendril.interests import Platform
        p = Platform(get_interest(id=1, session=session))
        p.add_child(self._interest.model_instance, auth_user=1, session=session)
        self._interest.activate(auth_user=1, session=session)


def load(manager):
    pass
