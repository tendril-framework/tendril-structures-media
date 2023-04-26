

import os
import json
from typing import Optional
from pydantic.dataclasses import dataclass
from dataclasses import asdict
from pydantic.json import pydantic_encoder


@dataclass
class MediaFileGeneralInfo(object):
    container: str
    file_size: int
    writing_application: Optional[str]
    internet_media_type: str            # Missing in WebP


def _strip_nones(nested_dict: dict):
    for k in list(nested_dict.keys()):
        v = nested_dict[k]
        if v is None:
            nested_dict.pop(k)
        if isinstance(v, dict):
            nested_dict[k] = _strip_nones(v)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _strip_nones(item)
    return nested_dict


@dataclass
class MediaFileInfo(object):
    original_filename: str
    ext: str

    def asdict(self):
        return _strip_nones(asdict(self))

    def json(self):
        return json.dumps(self.asdict(), indent=2,
                          default=pydantic_encoder)

    def width(self):
        raise NotImplementedError

    def height(self):
        raise NotImplementedError


class MediaFileInfoParser(object):
    info_class = MediaFileInfo

    def _parse(self, file):
        rv = {'original_filename': os.path.split(file.name)[1],
              'ext': os.path.splitext(file.name)[1]}
        return rv

    def parse(self, file):
        return self.info_class(**self._parse(file))
