import abc
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol, Any, Optional, TYPE_CHECKING

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import DesignStrength
from structure_scripts.aisc_360_10.elements_latex import AreaPropertiesLatex
from structure_scripts.aisc_360_10.helpers import (
    ConstructionType,
    _member_slenderness_limit,
)
from structure_scripts.shared.helpers import radius_of_gyration
from structure_scripts.aisc_360_10.section_slenderness import (
    FlangeWebSlenderness,
    ElementSlenderness,
)
from structure_scripts.shared.data import extract_input_dataframe
from structure_scripts.shared.materials import IsotropicMaterial
from structure_scripts.shared.sections import AreaProperties

if TYPE_CHECKING:
    from beams import BeamAnalysis, Beam
#
#
# class WebArea(Protocol):
#     """Extra area"""
#
#     web_area_major_axis: Quantity
#     web_area_minor_axis: Quantity
#
#
# class WebShearParameters(Protocol):
#     web_shear_coefficient_major_axis: float
#     web_shear_buckling_coefficient_major_axis: float
#     web_shear_coefficient_minor_axis: float
#     web_shear_buckling_coefficient_minor_axis: float
#

# class AreaProperties(Protocol):
#     area: Quantity
#     major_axis_inertia: Quantity
#     major_axis_elastic_section_modulus: Quantity
#     major_axis_plastic_section_modulus: Quantity
#     major_axis_radius_of_gyration: Quantity
#     minor_axis_inertia: Quantity
#     minor_axis_elastic_section_modulus: Quantity
#     minor_axis_plastic_section_modulus: Quantity
#     minor_axis_radius_of_gyration: Quantity
#     torsional_constant: Quantity
#     torsional_radius_of_gyration: Quantity
#     warping_constant: Quantity
#
#     # Don't be mad future me. At least it worked
#     def table(self, filter_names: list[str] = None):
#         return extract_input_dataframe(obj=self, extraction_type=AreaProperties, filter_names=filter_names)
#
#     @cached_property
#     def data_table_df(self):
#         return self.table(filter_names=["torsional_radius_of_gyration", "warping_constant"])
#
#     @cached_property
#     def latex(self):
#         return AreaPropertiesLatex(data=self)


# class AreaPropertiesWithWeb(AreaProperties, WebArea):
#     ...


class Section(Protocol):
    area_properties: AreaProperties
    material: IsotropicMaterial
    construction: ConstructionType

    @property
    @abc.abstractmethod
    def slenderness(self) -> FlangeWebSlenderness | ElementSlenderness:
        ...

    def compression(self, beam: "Beam") -> DesignStrength:
        ...

    def shear_major_axis(self, beam: "Beam") -> DesignStrength:
        ...


#
# class WithTorsionalBuckling(Protocol):
#     def torsional_buckling_critical_stress_effective_length(
#         self, beam: "BeamAnalysis"
#     ) -> Quantity:
#         ...
#
#
# class WithLateralTorsionalBuckling(Protocol):
#     effective_radius_of_gyration: Quantity
#     limit_length_torsional_buckling: Quantity
#
#
# class SectionWithWebAndFlange(Section, Protocol):
#     web_shear_coefficient: float
#     web_shear_buckling_coefficient: float
#     web_shear_coefficient_limit_0: float
#     web_plate_shear_buckling_coefficient: float
#     slenderness: FlangeWebSlenderness
#
#
# class SectionProfileWebFlangeTorsBuck(
#     SectionWithWebAndFlange, WithTorsionalBuckling, Protocol
# ):
#     ...
#
#
# class SectionWebFlangeTorsAndLatTorsBuck(
#     SectionProfileWebFlangeTorsBuck, WithLateralTorsionalBuckling, Protocol
# ):
#     ...
#
#
# @dataclass
# class GenericAreaProperties:
#     area: Quantity
#     major_axis_inertia: Quantity
#     major_axis_elastic_section_modulus: Quantity
#     minor_axis_inertia: Quantity
#     minor_axis_elastic_section_modulus: Quantity
#     torsional_constant: Quantity
#     warping_constant: Quantity | None = None
#     major_axis_plastic_section_modulus: Quantity | None = None
#     minor_axis_plastic_section_modulus: Quantity | None = None
#     major_axis_radius_of_gyration: Quantity | None = None
#     minor_axis_radius_of_gyration: Quantity | None = None
#     torsional_radius_of_gyration: Quantity | None = None
#
#     def __post_init__(self):
#         if not self.major_axis_plastic_section_modulus:
#             self.major_axis_plastic_section_modulus = (
#                 self.major_axis_elastic_section_modulus
#             )
#         if not self.minor_axis_plastic_section_modulus:
#             self.minor_axis_plastic_section_modulus = (
#                 self.minor_axis_elastic_section_modulus
#             )
#         if not self.minor_axis_radius_of_gyration:
#             self.minor_axis_radius_of_gyration = radius_of_gyration(
#                 self.minor_axis_inertia, self.area
#             )
#         if not self.major_axis_radius_of_gyration:
#             self.major_axis_radius_of_gyration = radius_of_gyration(
#                 self.major_axis_inertia, self.area
#             )
#         if not self.torsional_radius_of_gyration:
#             self.torsional_radius_of_gyration = radius_of_gyration(
#                 self.torsional_constant, self.area
#             )
