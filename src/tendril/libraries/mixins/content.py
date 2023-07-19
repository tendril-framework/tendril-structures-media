

from tendril.apiserver.templates.content import InterestContentRouterGenerator
from tendril.structures.content import content_models
from tendril.structures.content import content_types


class ContentLibraryMixin(object):
    media_types_allowed = content_types
    _additional_api_generators = [InterestContentRouterGenerator]

    def __init__(self, *args, **kwargs):
        super(ContentLibraryMixin, self).__init__(*args, **kwargs)
        self._accepted_types = None

    @property
    def accepted_types(self):
        if not self._accepted_types:
            library_allowed_types = self.media_types_allowed
            if library_allowed_types:
                accepted_types = content_types.intersection(library_allowed_types)
            else:
                accepted_types = content_types
            self._accepted_types = {k: v
                                    for (k, v) in content_models.items()
                                    if k in accepted_types}
        return self._accepted_types
