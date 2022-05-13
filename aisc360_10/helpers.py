from enum import Enum
from typing import Collection

import numpy as np

from quantities import Quantity, dimensionless


def same_units_simplify(q1: Quantity, q2: Quantity):
    q1 = q1.simplified
    q2 = q2.simplified
    if not q1.units == q2.units:
        raise ValueError("q1 and q2 don't have the same units")
    return q1, q2


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
