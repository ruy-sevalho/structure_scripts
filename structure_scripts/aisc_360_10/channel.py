from dataclasses import dataclass
from functools import cached_property
from typing import Union

from structure_scripts.helpers import (
    rectangle_area,
    self_inertia,
    transfer_inertia,
    section_modulus,
    radius_of_gyration,
    areas_centroid,
)
from structure_scripts.sections import ChannelDimensions
from structure_scripts.section_properties import AreaProperties
from structure_scripts.aisc_360_10.helpers import (
    _channel_area,
)


@dataclass
class Channel:
    dimensions: ChannelDimensions
    area_properties: AreaProperties

    # @cached_property
    # def slenderness(self) -> FlangeWebSlenderness:
    #     # TODO
    #     return
