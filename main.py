# Module for calculating beam in accordance to ANSI/AISC 360-10
# Author: Ruy Sevalho Goncalves

from dataclasses import dataclass
from functools import cached_property
from enum import Enum
from typing import Protocol

import numpy as np
import pandas as pd

from quantities import Quantity, dimensionless, cm, UnitQuantity, m, mm, GPa, MPa, N
from helpers import same_units_simplify
from criteria import SafetyFactor, SafetyFactorType

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")


class ConstructionType(str, Enum):
    ROLLED = "ROLLED"
    BUILT_UP = "BUILT_UP"


class Slenderness(str, Enum):
    SLENDER = "SLENDER"
    NON_SLENDER = "NON_SLENDER"
    COMPACT = "COMPACT"
    NON_COMPACT = "NON_COMPACT"


def _ratio_simplify(q1: Quantity, q2: Quantity) -> float:
    r: Quantity = (q1 / q2).simplified
    if not r.units == dimensionless:
        raise ValueError("q1/q2 is not dimensionless")
    return r.magnitude


# E2. EFFECTIVE LENGTH
def _member_slenderness_ratio(factor_k: float, unbraced_length: Quantity, radius_of_gyration: Quantity) -> float:
    n = _ratio_simplify(unbraced_length, radius_of_gyration)
    return factor_k * n


# E3. FLEXURAL BUCKLING OF MEMBERS WITHOUT SLENDER ELEMENTS (E3-1)
def _nominal_compressive_strength(critical_stress: Quantity, sectional_area: Quantity) -> Quantity:
    return critical_stress * sectional_area


def _critical_compression_stress_buckling_default(
        member_slenderness: float,
        modulus_linear: Quantity,
        yield_stress: Quantity,
        elastic_buckling_stress: Quantity
) -> Quantity:
    member_slenderness_limit: Quantity = 4.71 * (modulus_linear / yield_stress) ** 0.5
    member_slenderness_limit = member_slenderness_limit.simplified
    if member_slenderness <= member_slenderness_limit.magnitude:
        # (E3-2)
        ratio = _ratio_simplify(yield_stress, elastic_buckling_stress)
        return 0.658 ** ratio * yield_stress
    # (E3-3)
    return 0.877 * elastic_buckling_stress


# E(3-4)
def _elastic_flexural_buckling_stress(modulus_linear: Quantity, member_slenderness_ratio: float) -> Quantity:
    return np.pi ** 2 * modulus_linear / member_slenderness_ratio ** 2


# (E4-4)
def _elastic_torsional_buckling_stress_doubly_symmetric_member(
        modulus_linear: Quantity,
        modulus_shear: Quantity,
        effective_length_factor_torsional_buckling: float,
        member_length: Quantity,
        torsional_constant: Quantity,
        major_axis_inertia: Quantity,
        minor_axis_inertia: Quantity,
        warping_constant: Quantity
) -> Quantity:
    return (
            (np.pi ** 2 * modulus_linear * warping_constant /
             (effective_length_factor_torsional_buckling * member_length) ** 2
             + modulus_shear * torsional_constant)
            * (1 / (minor_axis_inertia + major_axis_inertia)
               )
    )


# Note of page Sect. E4.] TORSIONAL AND FLEXURAL-TORSIONAL BUCKLING OF MEMBERS
def _warping_constant(moment_of_inertia: Quantity, distance_between_flanges_centroid: Quantity):
    return moment_of_inertia * distance_between_flanges_centroid ** 2 / 4


# ANSI/AISC 360-10 page 16.1–16 (reference rules)
def _kc_coefficient(web_height: Quantity, web_thickness: Quantity):
    ratio = _ratio_simplify(web_height, web_thickness)
    return min((max((4 / ratio ** 0.5, 0.35)), 0.76))


# ANSI/AISC 360-10 page 16.1–16 (reference rules)
def _limit_ratio_default(modulus_linear: Quantity, stress: Quantity, factor: float, kc_coefficient: float = 1):
    ratio = _ratio_simplify(modulus_linear, stress)
    return factor * (kc_coefficient * ratio) ** (1 / 2)


# ANSI/AISC 360-10 page 16.1–17
def _limit_stress_built_up_sections(
        yield_stress: Quantity,
        section_modulus_tension: Quantity,
        section_modulus_compression: Quantity
):
    ratio = section_modulus_tension / section_modulus_compression
    if ratio >= 0.7:
        return 0.7 * yield_stress
    return min((yield_stress * ratio, yield_stress * 0.5))


def _flexural_slenderness_per_element(limit_slender: float, limit_compact: float, ratio: float) -> "Slenderness":
    if ratio < limit_compact:
        return Slenderness.COMPACT
    elif ratio < limit_slender:
        return Slenderness.NON_COMPACT
    else:
        return Slenderness.SLENDER


def _flexural_slenderness_several_elements(slenderness_list: list["Slenderness"]) -> "Slenderness":
    if Slenderness.SLENDER in slenderness_list:
        return Slenderness.SLENDER
    elif Slenderness.NON_COMPACT in slenderness_list:
        return Slenderness.NON_COMPACT
    else:
        return Slenderness.COMPACT


def _lateral_torsional_buckling_modification_factor_default(
        moment_max: Quantity,
        moment_a: Quantity,
        moment_b: Quantity,
        moment_c: Quantity
):
    numerator = 12.5 * moment_max
    denominator = 2.5 * moment_max + 3 * moment_a + 4 * moment_b + 3 * moment_c
    return _ratio_simplify(numerator, denominator)


def _flexural_yield_strength(yield_stress: Quantity, section_modulus: Quantity) -> Quantity:
    return yield_stress * section_modulus


def _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
        mod_factor: float,
        plastic_moment: Quantity,
        yield_stress: Quantity,
        section_modulus: Quantity,
        length_between_braces: Quantity,
        limiting_length_yield: Quantity,
        limiting_length_torsional_buckling: Quantity,
) -> Quantity:
    a = 1
    l_factor = (
            (length_between_braces - limiting_length_yield).simplified /
            (limiting_length_torsional_buckling - limiting_length_yield).simplified
    )
    mp_factor = plastic_moment - 0.7 * yield_stress * section_modulus
    calculated_moment = mod_factor * (plastic_moment - mp_factor * l_factor)
    momt_calc, momt_plastic = same_units_simplify(calculated_moment, plastic_moment)
    return min(momt_calc, momt_plastic)


def _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
        plastic_moment: Quantity,
        section_modulus: Quantity,
        critical_stress: Quantity
) -> Quantity:
    return critical_stress * section_modulus


def _flexural_lateral_torsional_buckling_strength_compact(
        case_b: Quantity,
        case_c: Quantity,
        length_between_braces: Quantity,
        limiting_length_yield: Quantity,
        limiting_length_torsional_buckling: Quantity,
) -> Quantity | None:
    if length_between_braces <= limiting_length_yield:
        return None
    elif length_between_braces <= limiting_length_torsional_buckling:
        return case_b
    return case_c


def _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
        mod_factor: float,
        length_between_braces: Quantity,
        modulus: Quantity,
        effective_radius_of_gyration: Quantity,
        coefficient_c: float,
        torsional_constant: Quantity,
        section_modulus: Quantity,
        distance_between_flange_centroids: Quantity,
) -> Quantity:
    ratio = (length_between_braces / effective_radius_of_gyration) ** 2
    first_term = (mod_factor * np.pi ** 2 * modulus) / ratio
    second_term = (
                          1 + 0.078 * torsional_constant * coefficient_c /
                          (section_modulus * distance_between_flange_centroids) * ratio
                  ) ** 0.5
    return first_term * second_term


def _limiting_length_yield(radius_of_gyration: Quantity, modulus: Quantity, yield_stress: Quantity) -> Quantity:
    return 1.76 * radius_of_gyration * (modulus / yield_stress) ** 0.5


def _limiting_length_torsional_buckling(
        modulus: Quantity,
        yield_stress: Quantity,
        section_modulus: Quantity,
        torsional_constant: Quantity,
        effective_radius_of_gyration: Quantity,
        distance_between_centroids: Quantity,
        coefficient_c: float,
) -> Quantity:
    ratio = torsional_constant * coefficient_c / (section_modulus * distance_between_centroids)
    inner_root = (ratio ** 2 + 6.76 * (0.7 * yield_stress / modulus) ** 2) ** 0.5
    outer_root = (ratio + inner_root) ** 0.5
    return 1.95 * effective_radius_of_gyration * modulus / (0.7 * yield_stress) * outer_root


def _effective_radius_of_gyration(
        major_section_modulus: Quantity, minor_inertia: Quantity, warping_constant: Quantity
) -> Quantity:
    return ((minor_inertia * warping_constant) ** 0.5 / major_section_modulus) ** 0.5


def _flexural_flange_local_buckling_non_compact(
        plastic_moment: Quantity,
        yield_stress: Quantity,
        section_modulus: Quantity,
        flange_ratio: float,
        compact_limit_ratio: float,
        slender_limit_ratio: float
) -> Quantity:
    ratio = (flange_ratio - slender_limit_ratio) / (compact_limit_ratio - slender_limit_ratio)
    return plastic_moment - (plastic_moment - 0.7 * yield_stress * section_modulus) * ratio


class Material(Protocol):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity


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


@dataclass
class DoublySymmetricIDimensionsUserDefined(DoublySymmetricIDimensions):
    flange_width: Quantity
    flange_thickness: Quantity
    web_height: Quantity
    web_thickness: Quantity
    total_height: Quantity

    @cached_property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness


@dataclass
class DoublySymmetricIAreaProperties(AreaProperties):
    dimensions: DoublySymmetricIDimensions


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

    def __post_init__(self):
        if not self.major_axis_plastic_section_modulus:
            self.major_axis_plastic_section_modulus = self.major_axis_elastic_section_modulus
        if not self.minor_axis_plastic_section_modulus:
            self.minor_axis_plastic_section_modulus = self.minor_axis_elastic_section_modulus

    @cached_property
    def major_axis_radius_of_gyration(self) -> Quantity:
        return (self.major_axis_inertia / self.area) ** 0.5

    @cached_property
    def minor_axis_radius_of_gyration(self) -> Quantity:
        return (self.minor_axis_inertia / self.area) ** 0.5

    @cached_property
    def torsional_radius_of_gyration(self) -> Quantity:
        return (self.torsional_constant / self.area) ** 0.5


class SlendernessAreaProperties(Protocol):
    major_axis_section_modulus: Quantity
    minor_axis_section_modulus: Quantity


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
    area_properties: AreaProperties
    dimensions: DoublySymmetricIDimensions
    material: Material
    construction: ConstructionType = ConstructionType.ROLLED
    coefficient_c = 1.0

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
                "strength_flexural_buckling": [SafetyFactor(
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


@dataclass
class BeamFlexureDoublySymmetric:
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity
    moment_max: Quantity | None = None
    moment_quarter: Quantity | None = None
    moment_center: Quantity | None = None
    moment_three_quarter: Quantity | None = None

    @cached_property
    def mod_factor(self):
        if None in (self.moment_max, self.moment_quarter, self.moment_center, self.moment_three_quarter):
            return 1.0
        return _lateral_torsional_buckling_modification_factor_default(
            self.moment_max,
            self.moment_quarter,
            self.moment_center,
            self.moment_three_quarter
        )

    @cached_property
    def plastic_moment(self) -> Quantity:
        return self.strength_yielding

    @cached_property
    def strength_yielding(self):
        return _flexural_yield_strength(
            self.profile.material.yield_stress,
            self.profile.area_properties.major_axis_plastic_section_modulus
        )

    @cached_property
    def strength_lateral_torsion_compact_case_b(self):
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.unbraced_length,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
            limiting_length_yield=self.profile.limit_length_yield,
            mod_factor=self.mod_factor,
            plastic_moment=self.plastic_moment,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def critical_stress_lateral_torsional_buckling(self):
        return _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=self.mod_factor,
            length_between_braces=self.unbraced_length,
            modulus=self.profile.material.modulus_linear,
            coefficient_c=self.profile.coefficient_c,
            distance_between_flange_centroids=self.profile.dimensions.distance_between_centroids,
            effective_radius_of_gyration=self.profile.effective_radius_of_gyration,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.profile.area_properties.torsional_constant
        )

    @cached_property
    def strength_lateral_torsion_compact_case_c(self):
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.plastic_moment,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            critical_stress=self.critical_stress_lateral_torsional_buckling,
        )

    @cached_property
    def strength_lateral_torsion(self):
        return _flexural_lateral_torsional_buckling_strength_compact(
            case_b=self.strength_lateral_torsion_compact_case_b,
            case_c=self.strength_lateral_torsion_compact_case_c,
            length_between_braces=self.unbraced_length,
            limiting_length_yield=self.profile.limit_length_yield,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
        )

    @cached_property
    def strength_flange_local_buckling_non_compact(self):
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange_flexural_compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange_flexural_major_axis_slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange_ratio,
            plastic_moment=self.plastic_moment,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def strength_flange_local_buckling(self):
        # TODO Implement slender flange local buckling strength
        return self.strength_flange_local_buckling_non_compact

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength yield": [SafetyFactor(
                    theoretical_limit_value=self.strength_yielding,
                    safety_factor=1.67,
                    type_=SafetyFactorType.ASD,
                ).allowable_value.rescale(kN * m)],
                "strength lateral torsion": [SafetyFactor(
                    theoretical_limit_value=self.strength_lateral_torsion,
                    safety_factor=1.67,
                    type_=SafetyFactorType.ASD,
                ).allowable_value.rescale(kN * m)],
                "strength flange local buckling": [SafetyFactor(
                    theoretical_limit_value=self.strength_flange_local_buckling,
                    safety_factor=1.67,
                    type_=SafetyFactorType.ASD,
                ).allowable_value.rescale(kN * m)]
            }
        )


# @dataclass
# class BeamCompressionFlexure:


def main():
    from pprint import pprint

    steel = IsoTropicMaterial(
        modulus_linear=200 * GPa,
        modulus_shear=77 * GPa,
        poisson_ratio=0.3,
        yield_stress=355 * MPa
    )
    area_properties_p004 = GenericAreaProperties(
        area=92.90 * cm ** 2,
        minor_axis_inertia=3880 * cm ** 4,
        minor_axis_elastic_section_modulus=306 * cm ** 3,
        minor_axis_plastic_section_modulus=463 * cm ** 3,
        major_axis_inertia=11282 * cm ** 4,
        major_axis_elastic_section_modulus=892 * cm ** 3,
        major_axis_plastic_section_modulus=986 * cm ** 3,
        torsional_constant=66 * cm ** 4,
    )
    dimensions_p004 = DoublySymmetricIDimensionsUserDefined(
        flange_width=250 * mm,
        flange_thickness=14.2 * mm,
        web_height=185 * mm,
        web_thickness=8.6 * mm,
        total_height=250 * mm
    )
    profile_p004 = DoublySymmetricIUserDefined(
        area_properties=area_properties_p004,
        dimensions=dimensions_p004,
        material=steel
    )
    beam_p004_length = 5.60 * m
    p004_flexure = BeamFlexureDoublySymmetric(
        profile=profile_p004,
        unbraced_length=beam_p004_length,
    )
    p004_compression = BeamCompressionEffectiveLength(
        profile=profile_p004,
        unbraced_length=beam_p004_length,
    )
    resume_c = p004_compression.strength_resume
    resume_f = p004_flexure.strength_resume
    resume = pd.concat([resume_c, resume_f], axis=1)
    pprint(
        p004_flexure.strength_resume
    )
    pprint(
        p004_compression.strength_resume
    )
    return resume


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    resume = main()
