from dataclasses import dataclass
from typing import Protocol, Any, Optional

from quantities import Quantity

from structure_scripts.aisc_360_10.helpers import _radius_of_gyration, ConstructionType
from structure_scripts.aisc_360_10.slenderness import FlangeWebSectionSlenderness
from structure_scripts.shared.materials import Material


class WebArea(Protocol):
    """Extra area"""
    web_area_major_axis: Quantity
    web_area_minor_axis: Quantity


class WebShearParameters(Protocol):
    web_shear_coefficient_major_axis: float
    web_shear_buckling_coefficient_major_axis: float
    web_shear_coefficient_minor_axis: float
    web_shear_buckling_coefficient_minor_axis: float


class AreaProperties(Protocol):
    area: Quantity
    major_axis_inertia: Quantity
    major_axis_elastic_section_modulus: Quantity
    major_axis_plastic_section_modulus: Quantity
    major_axis_radius_of_gyration: Quantity
    minor_axis_inertia: Quantity
    minor_axis_elastic_section_modulus: Quantity
    minor_axis_plastic_section_modulus: Quantity
    minor_axis_radius_of_gyration: Quantity
    torsional_constant: Quantity
    torsional_radius_of_gyration: Quantity
    warping_constant: Quantity

    # Don't be mad future me. At least it worked
    # def table(self, filter_names: list[str] = None):
    #     return extract_input_dataframe(obj=self, extraction_type=AreaProperties, filter_names=filter_names)
    #
    # @cached_property
    # def data_table_df(self):
    #     return self.table(filter_names=["torsional_radius_of_gyration", "warping_constant"])
    #
    # @cached_property
    # def latex(self):
    #     return AreaPropertiesLatex(data=self)


class AreaPropertiesWithWeb(AreaProperties, WebArea):
    ...


class SectionProfile(Protocol):
    area_properties: AreaProperties
    material: Material
    # coefficient_c: float
    effective_radius_of_gyration: Quantity
    warping_constant: Quantity
    construction: ConstructionType

    # web_shear_coefficient: float
    # web_shear_buckling_coefficient: float

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionTorsionalBuckling") -> Quantity:
        raise NotImplementedError


class WithTorsionalBuckling(Protocol):
    coefficient_c: float

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionTorsionalBuckling") -> Quantity:
        ...


class WithLateralTorsionBuckling(Protocol):
    coefficient_c: float


class SectionProfileWithWebAndFlange(SectionProfile, Protocol):
    area_properties: AreaPropertiesWithWeb
    material: Material
    effective_radius_of_gyration: Quantity
    warping_constant: Quantity
    web_shear_coefficient: float
    web_shear_buckling_coefficient: float
    web_shear_coefficient_limit_0: float
    slenderness: FlangeWebSectionSlenderness

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionFlexuralBuckling") -> Quantity:
        raise NotImplementedError


@dataclass
class GenericAreaPropertiesWithWeb(AreaProperties):
    area: Quantity
    web_area: Quantity
    major_axis_inertia: Quantity
    major_axis_elastic_section_modulus: Quantity
    minor_axis_inertia: Quantity
    minor_axis_elastic_section_modulus: Quantity
    torsional_constant: Quantity
    warping_constant: Quantity | None = None
    major_axis_plastic_section_modulus: Quantity | None = None
    minor_axis_plastic_section_modulus: Quantity | None = None
    major_axis_radius_of_gyration: Quantity | None = None
    minor_axis_radius_of_gyration: Quantity | None = None
    torsional_radius_of_gyration: Quantity | None = None

    def __post_init__(self):
        if not self.major_axis_plastic_section_modulus:
            self.major_axis_plastic_section_modulus = self.major_axis_elastic_section_modulus
        if not self.minor_axis_plastic_section_modulus:
            self.minor_axis_plastic_section_modulus = self.minor_axis_elastic_section_modulus
        if not self.minor_axis_radius_of_gyration:
            self.minor_axis_radius_of_gyration = _radius_of_gyration(self.minor_axis_inertia, self.area)
        if not self.major_axis_radius_of_gyration:
            self.major_axis_radius_of_gyration = _radius_of_gyration(self.major_axis_inertia, self.area)
        if not self.torsional_radius_of_gyration:
            self.torsional_radius_of_gyration = _radius_of_gyration(self.torsional_constant, self.area)