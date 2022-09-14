import uuid
from dataclasses import dataclass
from typing import runtime_checkable, Protocol, Any, Collection, Optional

import pandas as pd


@runtime_checkable
class DataClass(Protocol):
    def __dataclass_fields__(self):
        ...


def extract_input_dataframe(obj: Any, extraction_type: Any = None, filter_names: list[str] = None):
    extraction_type = extraction_type or obj
    filter_names = filter_names or []
    dict_ = {key: [getattr(obj, key)] for key in extraction_type.__annotations__.keys() if key not in filter_names}
    return pd.DataFrame(dict_)


def extract_dataframe(obj: Any, names: Collection[tuple[str, str]]):
    """Extracts a dataframe of attributes of objects. Names should be a collection of collection of a pair of strings.
     First str is the attribute name. The second is the index to use in pandas dataframe.
     """
    dict_ = {key: [getattr(obj, key)] for key in names}
    return pd.DataFrame(dict_)


@dataclass
class Unique:
    id: uuid.UUID = uuid.uuid4()
    name: Optional[str] = None