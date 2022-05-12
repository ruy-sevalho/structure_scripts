from functools import cached_property
from typing import Protocol, Any
from dataclasses import dataclass, field
import pandas as pd

from quantities import Quantity, UnitQuantity, cm, UnitQuantity, m, mm, GPa, MPa, N

from criteria import SafetyFactor, SafetyFactorType
from helpers import _areas_centroid, _critical_compression_stress_buckling_default, \
    _doubly_symmetric_i_torsional_constant, _effective_radius_of_gyration, _elastic_flexural_buckling_stress, \
    _elastic_torsional_buckling_stress_doubly_symmetric_member, _flexural_flange_local_buckling_non_compact, \
    _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric, \
    _flexural_lateral_torsional_buckling_strength_compact, \
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b, \
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c, _flexural_major_axis_yield_strength, \
    _flexural_minor_axis_yield_strength, _flexural_slenderness_per_element, _flexural_slenderness_several_elements, \
    _flexure_and_axial_compression_h1_1_criteria, _kc_coefficient, \
    _lateral_torsional_buckling_modification_factor_default, _limit_ratio_default, _limit_stress_built_up_sections, \
    _limiting_length_torsional_buckling, _limiting_length_yield, _member_slenderness_ratio, _minimum_allowed_strength, \
    _nominal_compressive_strength, _radius_of_gyration, _rectangle_area, _section_modulus, _self_inertia, \
    _transfer_inertia, _warping_constant, ConstructionType, Slenderness

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")


def _extract_dataframe(obj: Any, extraction_type: Any, filter_names: list[str] = None):
    filter_names = filter_names or []
    dict_ = {key: [getattr(obj, key)] for key in extraction_type.__annotations__.keys() if key not in filter_names}
    return pd.DataFrame(dict_)


class TableKeys(Protocol):
    @classmethod
    def table_keys(cls):
        return cls.__annotations__.keys()


class Material(Protocol):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity

    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=Material, filter_names=filter_names)

    @cached_property
    def default_table(self):
        return self.table(filter_names=["poisson_ratio"])


@dataclass
class IsoTropicMaterial(Material):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity
    density: Quantity | None = None


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
    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=AreaProperties, filter_names=filter_names)

    @cached_property
    def default_table(self):
        return self.table(filter_names=["warping_constant", "torsional_radius_of_gyration"])


class ProfileSlenderness(Protocol):
    axial_compression: Slenderness
    flexural_minor_axis: Slenderness
    flexural_major_axis: Slenderness


class SectionProfile(Protocol):
    area_properties: AreaProperties
    material: Material
    coefficient_c: float
    effective_radius_of_gyration: Quantity
    warping_constant: Quantity

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionEffectiveLength") -> Quantity:
        raise NotImplementedError


class DoublySymmetricIDimensions(Protocol):
    flange_width: Quantity
    flange_thickness: Quantity
    web_height: Quantity
    web_thickness: Quantity
    total_height: Quantity
    distance_between_centroids: Quantity

    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=DoublySymmetricIDimensions, filter_names=filter_names)

    @cached_property
    def default_table(self):
        return self.table()


@dataclass
class DoublySymmetricIAreaPropertiesFromDimensions(AreaProperties):
    dimensions: DoublySymmetricIDimensions

    # @cached_property
    # def table(self):
    #     return AreaProperties.table_keys()

    @cached_property
    def _flange_area(self):
        return _rectangle_area(width=self.dimensions.flange_width, height=self.dimensions.flange_thickness)

    @cached_property
    def _web_area(self):
        return _rectangle_area(width=self.dimensions.web_thickness, height=self.dimensions.web_height)

    @cached_property
    def area(self) -> Quantity:
        return self._web_area + 2 * self._flange_area

    @cached_property
    def _flange_self_inertia_major_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.flange_width, height=self.dimensions.flange_thickness)

    @cached_property
    def _flange_self_inertia_minor_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.flange_thickness, height=self.dimensions.flange_width)

    @cached_property
    def _web_self_inertia_major_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.web_thickness, height=self.dimensions.web_height)

    @cached_property
    def _web_self_inertia_minor_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.web_height, height=self.dimensions.web_thickness)

    @cached_property
    def _flange_area_centroid_major_axis(self):
        return self.dimensions.distance_between_centroids / 2

    @cached_property
    def _flange_transfer_inertia_major_axis(self):
        return _transfer_inertia(
            area=self._flange_area,
            center_to_na_distance=self._flange_area_centroid_major_axis
        )

    @cached_property
    def minor_axis_inertia(self):
        return 2 * self._flange_self_inertia_minor_axis + self._web_self_inertia_minor_axis

    @cached_property
    def major_axis_inertia(self):
        return 2 * self._flange_transfer_inertia_major_axis + 2 * self._flange_self_inertia_major_axis + self._web_self_inertia_major_axis

    @cached_property
    def major_axis_elastic_section_modulus(self) -> Quantity:
        return _section_modulus(self.major_axis_inertia, self.dimensions.total_height / 2)

    @cached_property
    def minor_axis_elastic_section_modulus(self) -> Quantity:
        return _section_modulus(self.minor_axis_inertia, self.dimensions.flange_width / 2)

    @cached_property
    def major_axis_radius_of_gyration(self) -> Quantity:
        return _radius_of_gyration(moment_of_inertia=self.major_axis_inertia, gross_section_area=self.area)

    @cached_property
    def minor_axis_radius_of_gyration(self) -> Quantity:
        return _radius_of_gyration(moment_of_inertia=self.minor_axis_inertia, gross_section_area=self.area)

    @cached_property
    def warping_constant(self):
        return _warping_constant(
            moment_of_inertia=self.minor_axis_inertia,
            distance_between_flanges_centroid=self.dimensions.distance_between_centroids
        )

    @cached_property
    def torsional_constant(self) -> Quantity:
        return _doubly_symmetric_i_torsional_constant(
            flange_width=self.dimensions.flange_width,
            total_height=self.dimensions.total_height,
            flange_thickness=self.dimensions.flange_thickness,
            web_thickness=self.dimensions.web_thickness
        )

    @cached_property
    def torsional_radius_of_gyration(self):
        return _radius_of_gyration(
            moment_of_inertia=self.torsional_constant,
            gross_section_area=self.area
        )

    @cached_property
    def _major_axis_plastic_half_centroid(self) -> Quantity:
        return _areas_centroid(
            (
                (self._flange_area, self._flange_area_centroid_major_axis),
                (self._web_area / 2, self.dimensions.web_height / 4)
            )
        )

    @cached_property
    def _major_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self._web_area / 2

    @cached_property
    def major_axis_plastic_section_modulus(self):
        return 2 * self._major_axis_plastic_half_centroid * self._major_axis_plastic_half_area

    @cached_property
    def _minor_axis_plastic_half_centroid(self) -> Quantity:
        return _areas_centroid(
            (
                (self._flange_area, self.dimensions.flange_width / 4),
                (self._web_area / 2, self.dimensions.web_thickness / 4)
            )
        )

    @cached_property
    def _minor_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self._web_area / 2

    @cached_property
    def minor_axis_plastic_section_modulus(self):
        return 2 * self._minor_axis_plastic_half_area * self._minor_axis_plastic_half_centroid


@dataclass
class DoublySymmetricIDimensionsUserDefined(DoublySymmetricIDimensions):
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Quantity
    web_height: Quantity | None = None

    def __post_init__(self):
        if not self.web_height:
            self.web_height = self.total_height - 2 * self.flange_thickness

    @cached_property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness


@dataclass
class GenericAreaProperties(AreaProperties):
    area: Quantity
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


@dataclass
class DoublySymmetricISlenderness(ProfileSlenderness):
    area_properties: AreaProperties
    dimensions: DoublySymmetricIDimensions
    construction: ConstructionType
    material: Material

    @cached_property
    def kc_coefficient(self):
        return _kc_coefficient(web_height=self.dimensions.web_height, web_thickness=self.dimensions.web_thickness)

    @cached_property
    def flange_axial_limit_ratio_rolled(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=0.56,
        )

    @cached_property
    def flange_axial_limit_ratio_rolled_latex(self):
        return

    @cached_property
    def flange_axial_limit_ratio_built_up(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=0.64,
            kc_coefficient=self.kc_coefficient
        )

    @cached_property
    def flange_axial_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.flange_axial_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.flange_axial_limit_ratio_built_up
        }
        return table[self.construction]

    @cached_property
    def flange_ratio(self):
        return self.dimensions.flange_width / 2 / self.dimensions.flange_thickness

    @cached_property
    def flange_axial_compression_slenderness(self):
        limit = self.flange_axial_limit_ratio
        ratio = self.flange_ratio
        if ratio < limit:
            return Slenderness.NON_SLENDER
        return Slenderness.SLENDER

    @cached_property
    def web_axial_compression_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=1.49
        )

    @cached_property
    def web_ratio(self) -> float:
        return self.dimensions.web_height / self.dimensions.web_thickness

    @cached_property
    def web_axial_compression_slenderness(self):
        limit = self.web_axial_compression_limit_ratio
        ratio = self.web_ratio
        if ratio < limit:
            return Slenderness.NON_SLENDER
        return Slenderness.SLENDER

    @cached_property
    def flange_flexural_compact_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=0.38
        )

    @cached_property
    def flange_flexural_slender_limit_ratio_rolled(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=1.0
        )

    @cached_property
    def flange_flexural_slender_limit_ratio_built_up(self):
        stress = _limit_stress_built_up_sections(
            yield_stress=self.material.yield_stress,
            section_modulus_tension=self.area_properties.major_axis_elastic_section_modulus,
            section_modulus_compression=self.area_properties.major_axis_elastic_section_modulus,
        )
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=stress,
            factor=0.95,
            kc_coefficient=self.kc_coefficient
        )

    @cached_property
    def flange_flexural_major_axis_slender_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.flange_flexural_slender_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.flange_flexural_slender_limit_ratio_built_up
        }
        return table[self.construction]

    @cached_property
    def flange_flexural_minor_axis_slender_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=1
        )

    @cached_property
    def flange_flexural_minor_axis_slenderness(self):
        limit_slender = self.flange_flexural_minor_axis_slender_limit_ratio
        limit_compact = self.flange_flexural_compact_limit_ratio
        ratio = self.flange_ratio
        return _flexural_slenderness_per_element(limit_slender=limit_slender, limit_compact=limit_compact, ratio=ratio)

    @cached_property
    def flange_flexural_major_axis_slenderness(self):
        limit_slender = self.flange_flexural_major_axis_slender_limit_ratio
        limit_compact = self.flange_flexural_compact_limit_ratio
        ratio = self.flange_ratio
        return _flexural_slenderness_per_element(limit_slender=limit_slender, limit_compact=limit_compact, ratio=ratio)

    @cached_property
    def web_flexural_slenderness(self):
        limit_slender = self.web_flexural_slender_limit_ratio
        limit_compact = self.web_flexural_compact_limit_ratio
        ratio = self.web_ratio
        return _flexural_slenderness_per_element(limit_slender=limit_slender, limit_compact=limit_compact, ratio=ratio)

    @cached_property
    def web_flexural_compact_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=3.76
        )

    @cached_property
    def web_flexural_slender_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=5.7
        )

    @cached_property
    def flexural_major_axis(self):
        slenderness_list = [
            self.flange_flexural_major_axis_slenderness,
            self.web_axial_compression_slenderness
        ]
        return _flexural_slenderness_several_elements(slenderness_list)

    @cached_property
    def flexural_minor_axis(self):
        slenderness_list = [
            self.flange_flexural_minor_axis_slenderness,
            self.web_axial_compression_slenderness
        ]
        return _flexural_slenderness_several_elements(slenderness_list)

    @cached_property
    def axial_compression(self):
        slenderness = [
            self.flange_axial_compression_slenderness,
            self.web_axial_compression_slenderness
        ]
        if Slenderness.SLENDER in slenderness:
            return Slenderness.SLENDER
        return Slenderness.NON_SLENDER


@dataclass
class DoublySymmetricIUserDefined(SectionProfile):
    dimensions: DoublySymmetricIDimensions
    material: Material
    area_properties: AreaProperties | None = None
    construction: ConstructionType = ConstructionType.ROLLED
    coefficient_c = 1.0

    def __post_init__(self):
        if not self.area_properties:
            self.area_properties = DoublySymmetricIAreaPropertiesFromDimensions(self.dimensions)

    @cached_property
    def default_table(self):
        dimensions_table = self.dimensions.default_table
        area_properties_table = self.area_properties.default_table
        extra_table = _extract_dataframe(
            obj=self,
            extraction_type=DoublySymmetricIUserDefined,
            filter_names=["dimensions", "area_properties", "material"]
        )
        return pd.concat((dimensions_table, area_properties_table, extra_table), axis=1)

    @cached_property
    def warping_constant(self):
        if self.area_properties.warping_constant:
            return self.area_properties.warping_constant
        return _warping_constant(
            moment_of_inertia=self.area_properties.minor_axis_inertia,
            distance_between_flanges_centroid=self.dimensions.distance_between_centroids
        )

    @cached_property
    def effective_radius_of_gyration(self):
        return _effective_radius_of_gyration(
            major_section_modulus=self.area_properties.major_axis_elastic_section_modulus,
            minor_inertia=self.area_properties.minor_axis_inertia,
            warping_constant=self.warping_constant,
        )

    @cached_property
    def limit_length_torsional_buckling(self):
        return _limiting_length_torsional_buckling(
            modulus=self.material.modulus_linear,
            yield_stress=self.material.yield_stress,
            section_modulus=self.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.area_properties.torsional_constant,
            effective_radius_of_gyration=self.effective_radius_of_gyration,
            distance_between_centroids=self.dimensions.distance_between_centroids,
            coefficient_c=self.coefficient_c,
        )

    @cached_property
    def limit_length_yield(self):
        return _limiting_length_yield(
            modulus=self.material.modulus_linear,
            radius_of_gyration=self.area_properties.minor_axis_radius_of_gyration,
            yield_stress=self.material.yield_stress
        )

    @cached_property
    def slenderness(self):
        return DoublySymmetricISlenderness(
            area_properties=self.area_properties,
            dimensions=self.dimensions,
            construction=self.construction,
            material=self.material
        )

    def elastic_torsional_buckling_stress(self, beam: "BeamCompressionEffectiveLength"):
        return _elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.material.modulus_linear,
            modulus_shear=self.material.modulus_shear,
            effective_length_factor_torsional_buckling=beam.factor_k_torsion,
            member_length=beam.unbraced_length,
            torsional_constant=self.area_properties.torsional_constant,
            major_axis_inertia=self.area_properties.major_axis_inertia,
            minor_axis_inertia=self.area_properties.minor_axis_inertia,
            warping_constant=self.warping_constant
        )

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionEffectiveLength"):
        return _critical_compression_stress_buckling_default(
            member_slenderness=beam.torsional_slenderness,
            modulus_linear=self.material.modulus_linear,
            yield_stress=self.material.yield_stress,
            elastic_buckling_stress=self.elastic_torsional_buckling_stress(beam),
        )


class BeamCompression(Protocol):
    strength_flexural_buckling: Quantity
    strength_torsional_buckling: Quantity


@dataclass
class BeamCompressionEffectiveLength(BeamCompression):
    profile: SectionProfile
    unbraced_length: Quantity
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0

    @cached_property
    def minor_axis_slenderness(self):
        return _member_slenderness_ratio(
            factor_k=self.factor_k_minor_axis,
            radius_of_gyration=self.profile.area_properties.minor_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length
        )

    @cached_property
    def torsional_slenderness(self):
        return _member_slenderness_ratio(
            factor_k=self.factor_k_torsion,
            unbraced_length=self.unbraced_length,
            radius_of_gyration=self.profile.area_properties.torsional_radius_of_gyration
        )

    @cached_property
    def elastic_flexural_buckling_stress(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.minor_axis_slenderness
        )

    @cached_property
    def flexural_buckling_critical_stress(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.minor_axis_slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress,
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def torsional_buckling_critical_stress(self):
        return self.profile.torsional_buckling_critical_stress_effective_length(self)

    @cached_property
    def strength_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_torsional_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.torsional_buckling_critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength flexural buckling": [SafetyFactor(
                    theoretical_limit_value=self.strength_flexural_buckling,
                    safety_factor=1.67,
                    type_=SafetyFactorType.ASD,
                ).allowable_value.rescale(kN)]
            }
        )


class BeamFlexure(Protocol):
    strength_yielding: Quantity
    strength_lateral_torsional_buckling: Quantity | None
    strength_compression_local_buckling: Quantity | None


class LateralTorsionalBucklingModificationFactor:
    moment_max: Quantity
    moment_quarter: Quantity
    moment_center: Quantity
    moment_three_quarter: Quantity

    @cached_property
    def mod_factor(self):
        return _lateral_torsional_buckling_modification_factor_default(
            self.moment_max,
            self.moment_quarter,
            self.moment_center,
            self.moment_three_quarter
        )


@dataclass
class BeamFlexureDoublySymmetric:
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity

    @cached_property
    def plastic_moment_major_axis(self) -> Quantity:
        return self.strength_major_axis_yield

    @cached_property
    def strength_major_axis_yield(self) -> Quantity:
        return _flexural_major_axis_yield_strength(
            self.profile.material.yield_stress,
            self.profile.area_properties.major_axis_plastic_section_modulus
        )

    def strength_lateral_torsion_compact_case_b(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.unbraced_length,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
            limiting_length_yield=self.profile.limit_length_yield,
            mod_factor=mod_factor,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    def critical_stress_lateral_torsional_buckling(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=mod_factor,
            length_between_braces=self.unbraced_length,
            modulus=self.profile.material.modulus_linear,
            coefficient_c=self.profile.coefficient_c,
            distance_between_flange_centroids=self.profile.dimensions.distance_between_centroids,
            effective_radius_of_gyration=self.profile.effective_radius_of_gyration,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.profile.area_properties.torsional_constant
        )

    def strength_lateral_torsion_compact_case_c(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            critical_stress=self.critical_stress_lateral_torsional_buckling(mod_factor),
        )

    def strength_lateral_torsion(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact(
            case_b=self.strength_lateral_torsion_compact_case_b(mod_factor),
            case_c=self.strength_lateral_torsion_compact_case_c(mod_factor),
            length_between_braces=self.unbraced_length,
            limiting_length_yield=self.profile.limit_length_yield,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
        )

    @cached_property
    def strength_major_axis_flange_local_buckling_slender(self):
        raise NotImplementedError

    @cached_property
    def strength_major_axis_flange_local_buckling_non_compact(self) -> Quantity:
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange_flexural_compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange_flexural_major_axis_slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange_ratio,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def strength_minor_axis_flange_local_buckling_non_compact(self) -> Quantity:
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange_flexural_compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange_flexural_minor_axis_slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange_ratio,
            plastic_moment=self.plastic_momento_minor_axis,
            section_modulus=self.profile.area_properties.minor_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    def strength_minor_axis_flange_local_buckling_slender(self):
        raise NotImplementedError

    @cached_property
    def strength_minor_axis_yield(self) -> Quantity:
        return _flexural_minor_axis_yield_strength(
            yield_stress=self.profile.material.yield_stress,
            elastic_section_modulus=self.profile.area_properties.minor_axis_elastic_section_modulus,
            plastic_section_modulus=self.profile.area_properties.minor_axis_plastic_section_modulus
        )

    @cached_property
    def plastic_momento_minor_axis(self) -> Quantity:
        return self.strength_minor_axis_yield

    @cached_property
    def strength_major_axis_flange_local_buckling(self) -> Quantity:
        # TODO Implement slender flange local buckling strength
        table = {
            Slenderness.COMPACT: None,
            Slenderness.NON_COMPACT: self.strength_major_axis_flange_local_buckling_non_compact,
            # Slenderness.SLENDER: self.strength_major_axis_flange_local_buckling_slender,
        }
        return table[self.profile.slenderness.flange_flexural_major_axis_slenderness]

    @cached_property
    def strength_minor_axis_flange_local_buckling(self) -> Quantity:
        # TODO Implement slender flange local buckling strength
        table = {
            Slenderness.COMPACT: None,
            Slenderness.NON_COMPACT: self.strength_minor_axis_flange_local_buckling_non_compact,
            Slenderness.SLENDER: self.strength_minor_axis_flange_local_buckling_slender,
        }
        return table[self.profile.slenderness.flange_flexural_major_axis_slenderness]

    def strength_major_axis(self, mod_factor: float = 1.) -> Quantity:
        yield_ = self.strength_major_axis_yield
        lateral_torsional_buckling = self.strength_lateral_torsion(mod_factor)
        flange_local_buckling = self.strength_major_axis_flange_local_buckling
        strengths = (yield_, lateral_torsional_buckling, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    def strength_minor_axis(self, mod_factor: float = 1.) -> Quantity:
        yield_ = self.strength_minor_axis_yield
        flange_local_buckling = self.strength_major_axis_flange_local_buckling
        strengths = (yield_, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    def strength_resume(self, mod_factor: float = 1.) -> pd.DataFrame:
        strength_local_buckling = self.strength_major_axis_flange_local_buckling
        df = {
            "strength yield": [SafetyFactor(
                theoretical_limit_value=self.strength_major_axis_yield,
                safety_factor=1.67,
                type_=SafetyFactorType.ASD,
            ).allowable_value.rescale(kN * m)],
            "strength lateral torsion": [SafetyFactor(
                theoretical_limit_value=self.strength_lateral_torsion(),
                safety_factor=1.67,
                type_=SafetyFactorType.ASD,
            ).allowable_value.rescale(kN * m)]
        }
        if strength_local_buckling:
            df.update(
                {
                    "strength lateral torsion": [SafetyFactor(
                        theoretical_limit_value=self.strength_lateral_torsion(mod_factor),
                        safety_factor=1.67,
                        type_=SafetyFactorType.ASD,
                    ).allowable_value.rescale(kN * m)]
                }
            )
        return pd.DataFrame(df)


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLength:
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0

    @cached_property
    def compression(self):
        return BeamCompressionEffectiveLength(
            profile=self.profile,
            unbraced_length=self.unbraced_length,
            factor_k_torsion=self.factor_k_torsion,
            factor_k_major_axis=self.factor_k_major_axis,
            factor_k_minor_axis=self.factor_k_minor_axis
        )

    @cached_property
    def flexure(self):
        return BeamFlexureDoublySymmetric(
            profile=self.profile,
            unbraced_length=self.unbraced_length,
        )

    def compression_flexure_combined_criteria_h1_1(
            self,
            required_axial_strength: Quantity,
            required_major_axis_flexure_strength: Quantity,
            required_minor_axis_flexure_strength: Quantity,
            lateral_torsional_buckling_modification_factor: float = 1.
    ) -> float:
        available_axial_strength = SafetyFactor(
            self.compression.strength_flexural_buckling,
            safety_factor=1.67,
            type_=SafetyFactorType.ASD
        ).allowable_value
        available_major_axis_strength = SafetyFactor(
            self.flexure.strength_major_axis(lateral_torsional_buckling_modification_factor),
            safety_factor=1.67,
            type_=SafetyFactorType.ASD
        ).allowable_value
        available_minor_axis_strength = SafetyFactor(
            self.flexure.strength_minor_axis(lateral_torsional_buckling_modification_factor),
            safety_factor=1.67,
            type_=SafetyFactorType.ASD
        ).allowable_value
        return _flexure_and_axial_compression_h1_1_criteria(
            available_axial_strength=available_axial_strength,
            required_axial_strength=required_axial_strength,
            available_major_axis_flexural_strength=available_major_axis_strength,
            required_major_axis_flexural_strength=required_major_axis_flexure_strength,
            available_minor_axis_flexural_strength=available_minor_axis_strength,
            required_minor_axis_flexural_strength=required_minor_axis_flexure_strength,
        )

    def resume(self, mod_factor=1.):
        return pd.concat((self.compression.strength_resume, self.flexure.strength_resume(mod_factor)), axis=1)
