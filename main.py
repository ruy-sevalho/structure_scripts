# Module for calculating beam in accordance to ANSI/AISC 360-10
# Author: Ruy Sevalho Goncalves

from dataclasses import dataclass, field, fields
from functools import cached_property
from enum import Enum
from typing import Protocol, Collection

import numpy as np
import pandas as pd
import pylatex as ltx

from quantities import Quantity, dimensionless, cm, UnitQuantity, m, mm, GPa, MPa, N
from helpers import same_units_simplify
from criteria import SafetyFactor, SafetyFactorType
from latex import _dataframe_table_columns

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")
LATEX_ABREVIATION = 'latex'


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


def _flexural_major_axis_yield_strength(yield_stress: Quantity, section_modulus: Quantity) -> Quantity:
    return yield_stress * section_modulus


def _flexural_minor_axis_yield_strength(
        yield_stress: Quantity, plastic_section_modulus: Quantity,
        elastic_section_modulus: Quantity
) -> Quantity:
    return min(yield_stress * plastic_section_modulus, 1.6 * yield_stress * elastic_section_modulus)


def _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
        mod_factor: float,
        plastic_moment: Quantity,
        yield_stress: Quantity,
        section_modulus: Quantity,
        length_between_braces: Quantity,
        limiting_length_yield: Quantity,
        limiting_length_torsional_buckling: Quantity,
) -> Quantity:
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


def _flexure_and_axial_compression_h1_1_validity(
        minor_axis_elastic_section_modulus: Quantity,
        minor_axis_compression_flange_elastic_section_modulus: Quantity
) -> bool:
    ratio = _ratio_simplify(minor_axis_compression_flange_elastic_section_modulus, minor_axis_elastic_section_modulus)
    return 0.1 <= ratio <= 0.9


def _flexure_and_axial_compression_h1_1_criteria(
        required_axial_strength: Quantity,
        available_axial_strength: Quantity,
        required_major_axis_flexural_strength: Quantity,
        available_major_axis_flexural_strength: Quantity,
        required_minor_axis_flexural_strength: Quantity,
        available_minor_axis_flexural_strength: Quantity,
) -> float:
    axial_strength_ratio = _ratio_simplify(required_axial_strength, available_axial_strength)
    minor_axis_ratio = _ratio_simplify(required_minor_axis_flexural_strength, available_minor_axis_flexural_strength)
    major_axis_ratio = _ratio_simplify(required_major_axis_flexural_strength, available_major_axis_flexural_strength)
    factor = 8. / 9. if axial_strength_ratio >= 0.2 else 1.
    denominator = 1. if axial_strength_ratio >= 0.2 else 2.
    return axial_strength_ratio / denominator + factor * (minor_axis_ratio + major_axis_ratio)


def _flexure_and_axial_compression_h1_3_validity(
        required_minor_axis_flexural_strength: Quantity,
        available_minor_axis_flexural_strength: Quantity
) -> bool:
    ratio = _ratio_simplify(required_minor_axis_flexural_strength, available_minor_axis_flexural_strength)
    return ratio >= 0.05


def _flexure_and_axial_compression_h1_3_criteria(
        required_axial_strength: Quantity,
        available_axial_strength: Quantity,
        required_major_axis_flexural_strength: Quantity,
        available_major_axis_flexural_strength: Quantity,
        mod_factor: float
) -> float:
    axial_strength_ratio = _ratio_simplify(required_axial_strength, available_axial_strength)
    flexural_strength_ratio = _ratio_simplify(
        required_major_axis_flexural_strength,
        available_major_axis_flexural_strength
    )
    return axial_strength_ratio * (1.5 + 0.5 * available_axial_strength) + (flexural_strength_ratio / mod_factor) ** 2


def _minimum_allowed_strength(strengths: Collection[Quantity]):
    strengths = filter(lambda x: x, strengths)
    return min(strengths)


def _radius_of_gyration(moment_of_inertia: Quantity, gross_section_area: Quantity):
    return (moment_of_inertia / gross_section_area) ** 0.5


def _self_inertia(width: Quantity, height: Quantity) -> Quantity:
    return width * height ** 3 / 12


def _transfer_inertia(area: Quantity, center_to_na_distance: Quantity) -> Quantity:
    return area * center_to_na_distance ** 2


def _rectangle_area(width: Quantity, height: Quantity) -> Quantity:
    return width * height


def _section_modulus(inertia: Quantity, max_distance_to_neutral_axis: Quantity) -> Quantity:
    return inertia / max_distance_to_neutral_axis


def _doubly_symmetric_i_torsional_constant(
        flange_width: Quantity,
        total_height: Quantity,
        flange_thickness: Quantity,
        web_thickness: Quantity
) -> Quantity:
    return (2 * flange_width * flange_thickness ** 3 + (total_height - flange_thickness) * web_thickness ** 3) / 3


def _areas_centroid(areas: Collection[tuple[Quantity, Quantity]]) -> Quantity:
    summation_weighted_areas = Quantity(0, "mm**3")
    summation_areas = Quantity(0, "mm**2")
    for area in areas:
        summation_weighted_areas = summation_weighted_areas + area[0] * area[1]
        summation_areas = summation_areas + area[0]
    return summation_weighted_areas / summation_areas


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

    @classmethod
    def table_keys(cls):
        return cls.__annotations__.keys()

    # Don't be mad future me. At least it worked
    @cached_property
    def table(self):
        return pd.DataFrame({key: [getattr(self, key)] for key in AreaProperties.table_keys()})


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
    dimensions: DoublySymmetricIDimensions
    material: Material
    area_properties: AreaProperties | None = None
    construction: ConstructionType = ConstructionType.ROLLED
    coefficient_c = 1.0

    def __post_init__(self):
        if not self.area_properties:
            self.area_properties = DoublySymmetricIAreaPropertiesFromDimensions(self.dimensions)

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


def main():
    steel = IsoTropicMaterial(
        modulus_linear=200 * GPa,
        modulus_shear=77 * GPa,
        poisson_ratio=0.3,
        yield_stress=355 * MPa
    )
    area_properties_wx250x250x73 = GenericAreaProperties(
        area=94.90 * cm ** 2,
        minor_axis_inertia=3883 * cm ** 4,
        minor_axis_elastic_section_modulus=306 * cm ** 3,
        minor_axis_plastic_section_modulus=463 * cm ** 3,
        major_axis_inertia=11508 * cm ** 4,
        major_axis_elastic_section_modulus=910 * cm ** 3,
        major_axis_plastic_section_modulus=1007 * cm ** 3,
        torsional_constant=66 * cm ** 4,
    )
    dimensions_wx250x250x73 = DoublySymmetricIDimensionsUserDefined(
        flange_width=250 * mm,
        flange_thickness=14.2 * mm,
        web_thickness=8.6 * mm,
        total_height=250 * mm
    )
    area_properties_w_arbitrary = GenericAreaProperties(
        area=5990 * mm ** 2,
        minor_axis_inertia=1270 * cm ** 4,
        minor_axis_elastic_section_modulus=127 * cm ** 3,
        minor_axis_plastic_section_modulus=195 * cm ** 3,
        major_axis_inertia=6470 * cm ** 4,
        major_axis_elastic_section_modulus=518 * cm ** 3,
        major_axis_plastic_section_modulus=584 * cm ** 3,
        torsional_constant=66 * cm ** 4,
    )
    # print(area_properties_w_arbitrary.table_keys())
    # print(area_properties_w_arbitrary.as_table())
    dimensions_w_arbitrary = DoublySymmetricIDimensionsUserDefined(
        flange_width=250 * mm,
        flange_thickness=9.5 * mm,
        web_thickness=9.5 * mm,
        total_height=250 * mm
    )
    profile_wx250x250x73 = DoublySymmetricIUserDefined(
        area_properties=area_properties_wx250x250x73,
        dimensions=dimensions_wx250x250x73,
        material=steel
    )
    profile_wx250x250x73_calculated = DoublySymmetricIUserDefined(
        dimensions=dimensions_wx250x250x73,
        material=steel
    )
    table_str = _dataframe_table_columns(
        profile_wx250x250x73_calculated.area_properties.table,
        unit_display="cell"
    )
    print(table_str.dumps())
    profile_arbitrary = DoublySymmetricIUserDefined(
        dimensions=dimensions_w_arbitrary,
        material=steel
    )
    beam_length = 2.60 * m
    beam_combined_10 = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_arbitrary,
        unbraced_length=beam_length
    )
    beam_combined_14 = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_wx250x250x73,
        unbraced_length=beam_length
    )
    required_axial_strength = 60 * kN
    required_major_axis_strength = 120 * kN * m
    required_minor_axis_strength = 0 * kN * m
    # print(profile_wx250x250x73.warping_constant.rescale(dm ** 6))
    # print(profile_wx250x250x73.dimensions.distance_between_centroids.rescale(mm))
    # print(profile_wx250x250x73.slenderness.flange_axial_limit_ratio)
    # print(profile_wx250x250x73.slenderness.flange_ratio)
    # print(profile_wx250x250x73.slenderness.web_axial_compression_limit_ratio)
    # print(profile_wx250x250x73.slenderness.web_ratio)
    # print(profile_wx250x250x73.area_properties.minor_axis_radius_of_gyration)
    # print("compression")
    # print(beam_compression.minor_axis_slenderness)
    # print((4.71 * (steel.modulus_linear / steel.yield_stress) ** 0.5).simplified)
    # print(beam_compression.elastic_flexural_buckling_stress)
    # print(beam_compression.flexural_buckling_critical_stress)
    # print(beam_compression.strength_flexural_buckling.rescale(kN))
    # print('flexure')
    # print(profile_wx250x250x73.slenderness.flange_flexural_compact_limit_ratio)
    # print(profile_wx250x250x73.slenderness.web_flexural_compact_limit_ratio)
    # print(beam_flexure.strength_major_axis_yield.rescale(kN * m))
    # print(profile_wx250x250x73.limit_length_yield.rescale(m))
    # print(profile_wx250x250x73.limit_length_torsional_buckling.rescale(m))
    # print(profile_wx250x250x73.warping_constant.rescale(cm ** 6))
    # print(profile_wx250x250x73.effective_radius_of_gyration.rescale(mm))

    # print("10 mm")
    # print(
    #     beam_combined_10.compression_flexure_combined_criteria_h1_1(
    #         required_axial_strength=required_axial_strength,
    #         required_major_axis_flexure_strength=required_major_axis_strength,
    #         required_minor_axis_flexure_strength=required_minor_axis_strength
    #     )
    # )
    # print("14 mm")
    # print(
    #     beam_combined_14.compression_flexure_combined_criteria_h1_1(
    #         required_axial_strength=required_axial_strength,
    #         required_major_axis_flexure_strength=required_major_axis_strength,
    #         required_minor_axis_flexure_strength=required_minor_axis_strength
    #     )
    # )
    return beam_combined_10, beam_combined_14


def print_obj_pairs_attributes(pair: tuple, attributes):
    for attribute in attributes:
        attrs = [getattr(obj, attribute) for obj in pair]
        print(f"{attribute}_1: {attrs[0]}")
        print(f"{attribute}_2: {attrs[1]}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    beam_10, beam_14 = main()
    # attrs = ('area', "minor_axis_inertia", "minor_axis_radius_of_gyration", "minor_axis_elastic_section_modulus",
    #          "minor_axis_plastic_section_modulus", "major_axis_inertia", "major_axis_radius_of_gyration",
    #          "major_axis_elastic_section_modulus",
    #          "major_axis_plastic_section_modulus", "torsional_constant")
    # print_obj_pairs_attributes((user_defined.area_properties, calculated.area_properties), attrs)
