from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

from .manager import ContentProviderManager
_manager = ContentProviderManager(prefix='tendril.structures.content.providers')

import sys
sys.modules[__name__] = _manager
_manager.finalize()
