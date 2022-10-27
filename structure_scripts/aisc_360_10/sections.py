from abc import abstractmethod
from typing import Protocol, TYPE_CHECKING, Union
from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    DesignType,
    StrengthType,
)
from structure_scripts.aisc_360_10.section_slenderness import (
    FlangeWebSlenderness,
)

if TYPE_CHECKING:
    pass
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

LoadReturn = Union[
    dict[StrengthType, Quantity],
    dict[StrengthType, dict[str, Union[Quantity, float, None]]],
]


class Section(Protocol):
    # material: IsotropicMaterial
    # construction: ConstructionType
    #
    # @property
    # @abstractmethod
    # def area_properties(self) -> AreaProperties:
    #     pass

    def compression_design_strength(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> tuple[Quantity, StrengthType]:
        ...

    def compression_nominal_strengths(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
        detailed_results: bool = False,
        # design_type: DesignType = DesignType.ASD,
    ) -> LoadReturn:
        ...

    def shear_major_axis_design_strength(
        self, design_type: DesignType = DesignType.ASD
    ) -> tuple[Quantity, StrengthType]:
        ...

    def shear_major_axis_nominal_strengths(
        self, detailed_results: bool = False
    ) -> LoadReturn:
        ...

    def shear_minor_axis_design_strength(
        self, design_type: DesignType = DesignType.ASD
    ) -> tuple[Quantity, StrengthType]:
        ...

    def shear_minor_axis_nominal_strengths(
        self, detailed_results: bool = False
    ) -> LoadReturn:
        ...

    def flexure_major_axis_design_strength(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> Quantity:
        ...

    def flexure_major_axis_nominal_strengths(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        detailed_results: bool = False,
    ) -> Quantity:
        ...

    def flexure_minor_axis_design_strength(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> Quantity:
        ...

    def flexure_minor_axis_nominal_strengths(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        detailed_results: bool = False,
    ) -> Quantity:
        ...


class HasWebFlange(Protocol):
    @property
    @abstractmethod
    def slenderness(self) -> FlangeWebSlenderness:
        pass


class SectionWithWebFlange(Section, HasWebFlange, Protocol):
    pass


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
