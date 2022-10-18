from dataclasses import dataclass
from functools import cached_property
from typing import Optional, Union

from quantities import Quantity

from structure_scripts.shared.sections import AreaProperties
from structure_scripts.aisc_360_10.helpers import _total_height, web_height, _channel_area
from structure_scripts.aisc_360_10.section_slenderness import FlangeWebSlenderness


@dataclass
class ChannelDimensions:
    """Channel section profile definition. Must specify either total height or web height but not both"""
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Optional[Quantity] = None
    web_height: Optional[Quantity] = None

    def __post_init__(self):
        if self.total_height and self.web_height:
            raise ValueError(f"Pass either total or web height, but not both")
        if not self.total_height and not self.web_height:
            raise ValueError("Must pass either total or web height, both can't be None")
        if not self.total_height:
            self.total_height = _total_height(web_height=self.web_height, flange_thickness=self.flange_thickness)
        else:
            self.web_height = web_height(total_height=self.total_height, flange_thickness=self.flange_thickness)


@dataclass
class ChannelAreaProperties(AreaProperties):
    dimensions: ChannelDimensions

    @cached_property
    def area(self):
        return _channel_area(
            web_height=self.dimensions.web_height,
            web_thickness=self.dimensions.web_thickness,
            flange_width=self.dimensions.flange_width,
            flange_thickness=self.dimensions.flange_thickness
        )

    @cached_property
    def major_axis_inertia(self):
        return


    # major_axis_inertia: Quantity
    # major_axis_elastic_section_modulus: Quantity
    # major_axis_plastic_section_modulus: Quantity
    # major_axis_radius_of_gyration: Quantity
    # minor_axis_inertia: Quantity
    # minor_axis_elastic_section_modulus: Quantity
    # minor_axis_plastic_section_modulus: Quantity
    # minor_axis_radius_of_gyration: Quantity
    # torsional_constant: Quantity
    # torsional_radius_of_gyration: Quantity
    # warping_constant: Quantity
    # web_area: Quantity

@dataclass
class Channel:
    dimensions: ChannelDimensions
    area_properties: Union[AreaProperties, None] = None

    @cached_property
    def slenderness(self) -> FlangeWebSlenderness:
        # TODO
        return
