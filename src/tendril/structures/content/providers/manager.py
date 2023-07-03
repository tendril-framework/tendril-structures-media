

import importlib

from .base import ContentProviderBase

from tendril.utils.versions import get_namespace_package_names
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class ContentProviderManager(object):
    def __init__(self, prefix):
        self._prefix = prefix
        self._providers = {}
        self._register_providers()
        self.finalized = False

    def _register_providers(self):
        logger.debug("Loading content providers from {0}".format(self._prefix))
        modules = list(get_namespace_package_names(self._prefix))
        for m_name in modules:
            if m_name == __name__:
                continue
            m = importlib.import_module(m_name)
            logger.debug("Loading content providers from {0}".format(m_name))
            m.load(self)

    def register_provider(self, provider : ContentProviderBase):
        self._providers[provider.name] = provider

    def finalize(self):
        for name, provider in self._providers.items():
            logger.info(f"Installing Content Provider '{name}'")
            provider.commit_to_db()
        self.finalized = True

    @property
    def registered_providers(self):
        return self._providers
