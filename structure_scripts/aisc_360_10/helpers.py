from enum import Enum
from typing import Collection

import numpy as np

from quantities import Quantity

from structure_scripts.aisc_360_10.section_slenderness import Slenderness
from structure_scripts.shared.helpers import ratio_simplify, same_units_simplify


class ConstructionType(str, Enum):
    ROLLED = "ROLLED"
    BUILT_UP = "BUILT_UP"


# E3. FLEXURAL BUCKLING OF MEMBERS WITHOUT SLENDER ELEMENTS (E3-1)
def _nominal_compressive_strength(
    critical_stress: Quantity, sectional_area: Quantity
) -> Quantity:
    return critical_stress * sectional_area


def _member_slenderness_limit(
    modulus_linear: Quantity,
    yield_stress: Quantity,
):
    member_slenderness_limit: Quantity = 4.71 * (modulus_linear / yield_stress) ** 0.5
    member_slenderness_limit = member_slenderness_limit.simplified
    return member_slenderness_limit.magnitude


def critical_compression_stress_buckling_default(
    member_slenderness: float,
    yield_stress: Quantity,
    elastic_buckling_stress: Quantity,
    # member_slenderness_limit: float,
) -> Quantity:
    if ratio_simplify(yield_stress, elastic_buckling_stress) <= 2.25:
        # (E3-2)
        ratio = ratio_simplify(yield_stress, elastic_buckling_stress)
        return 0.658**ratio * yield_stress
    # (E3-3)
    return 0.877 * elastic_buckling_stress


# E(3-4)
def elastic_flexural_buckling_stress(
    modulus_linear: Quantity, member_slenderness_ratio: float
) -> Quantity:
    return np.pi**2 * modulus_linear / member_slenderness_ratio**2


# (E4-4)
def elastic_torsional_buckling_stress_doubly_symmetric_member(
    modulus_linear: Quantity,
    modulus_shear: Quantity,
    effective_length_factor_torsional_buckling: float,
    member_length: Quantity,
    torsional_constant: Quantity,
    major_axis_inertia: Quantity,
    minor_axis_inertia: Quantity,
    warping_constant: Quantity,
) -> Quantity:
    return (
        np.pi**2
        * modulus_linear
        * warping_constant
        / (effective_length_factor_torsional_buckling * member_length) ** 2
        + modulus_shear * torsional_constant
    ) * (1 / (minor_axis_inertia + major_axis_inertia))


# Note of page Sect. E4.] TORSIONAL AND FLEXURAL-TORSIONAL BUCKLING OF MEMBERS
def warping_constant(
    moment_of_inertia: Quantity, distance_between_flanges_centroid: Quantity
):
    return moment_of_inertia * distance_between_flanges_centroid**2 / 4


# ANSI/AISC 360-10 page 16.1–16 (reference rules)
def kc_coefficient(web_height: Quantity, web_thickness: Quantity):
    ratio = ratio_simplify(web_height, web_thickness)
    return min((max((4 / ratio**0.5, 0.35)), 0.76))


# ANSI/AISC 360-10 page 16.1–16 (reference rules)
def limit_ratio_default(
    modulus_linear: Quantity, stress: Quantity, factor: float, kc_coefficient: float = 1
):
    ratio = ratio_simplify(modulus_linear, stress)
    return factor * (kc_coefficient * ratio) ** (1 / 2)


# ANSI/AISC 360-10 page 16.1–17
def limit_stress_built_up_sections(
    yield_stress: Quantity,
    section_modulus_tension: Quantity,
    section_modulus_compression: Quantity,
):
    ratio = section_modulus_tension / section_modulus_compression
    if ratio >= 0.7:
        return 0.7 * yield_stress
    return min((yield_stress * ratio, yield_stress * 0.5))


def flexural_slenderness_several_elements(
    slenderness_list: list["Slenderness"],
) -> "Slenderness":
    if Slenderness.SLENDER in slenderness_list:
        return Slenderness.SLENDER
    elif Slenderness.NON_COMPACT in slenderness_list:
        return Slenderness.NON_COMPACT
    else:
        return Slenderness.COMPACT


def lateral_torsional_buckling_modification_factor_default(
    moment_max: Quantity, moment_a: Quantity, moment_b: Quantity, moment_c: Quantity
):
    numerator = 12.5 * moment_max
    denominator = 2.5 * moment_max + 3 * moment_a + 4 * moment_b + 3 * moment_c
    return ratio_simplify(numerator, denominator)


def flexural_major_axis_yield_strength(
    yield_stress: Quantity, section_modulus: Quantity
) -> Quantity:
    return yield_stress * section_modulus


def _flexural_minor_axis_yield_strength(
    yield_stress: Quantity,
    plastic_section_modulus: Quantity,
    elastic_section_modulus: Quantity,
) -> Quantity:
    return min(
        yield_stress * plastic_section_modulus,
        1.6 * yield_stress * elastic_section_modulus,
    )


def _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
    mod_factor: float,
    plastic_moment: Quantity,
    yield_stress: Quantity,
    section_modulus: Quantity,
    length_between_braces: Quantity,
    limiting_length_yield: Quantity,
    limiting_length_torsional_buckling: Quantity,
) -> Quantity:
    l_factor = (length_between_braces - limiting_length_yield).simplified / (
        limiting_length_torsional_buckling - limiting_length_yield
    ).simplified
    mp_factor = plastic_moment - 0.7 * yield_stress * section_modulus
    calculated_moment = mod_factor * (plastic_moment - mp_factor * l_factor)
    momt_calc, momt_plastic = same_units_simplify(calculated_moment, plastic_moment)
    return min(momt_calc, momt_plastic)


def _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
    plastic_moment: Quantity, section_modulus: Quantity, critical_stress: Quantity
) -> Quantity:
    return critical_stress * section_modulus


def _flexural_lateral_torsional_buckling_strength(
    case_b: Quantity | str,
    case_c: Quantity | str,
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
    first_term = (mod_factor * np.pi**2 * modulus) / ratio
    second_term = (
        1
        + 0.078
        * torsional_constant
        * coefficient_c
        / (section_modulus * distance_between_flange_centroids)
        * ratio
    ) ** 0.5
    return first_term * second_term


def limiting_length_yield(
    radius_of_gyration: Quantity, modulus: Quantity, yield_stress: Quantity
) -> Quantity:
    return 1.76 * radius_of_gyration * (modulus / yield_stress) ** 0.5


def limiting_length_torsional_buckling(
    modulus: Quantity,
    yield_stress: Quantity,
    section_modulus: Quantity,
    torsional_constant: Quantity,
    effective_radius_of_gyration: Quantity,
    distance_between_centroids: Quantity,
    coefficient_c: float,
) -> Quantity:
    ratio = (
        torsional_constant
        * coefficient_c
        / (section_modulus * distance_between_centroids)
    )
    inner_root = (ratio**2 + 6.76 * (0.7 * yield_stress / modulus) ** 2) ** 0.5
    outer_root = (ratio + inner_root) ** 0.5
    return (
        1.95
        * effective_radius_of_gyration
        * modulus
        / (0.7 * yield_stress)
        * outer_root
    )


def effective_radius_of_gyration(
    major_section_modulus: Quantity, minor_inertia: Quantity, warping_constant: Quantity
) -> Quantity:
    return ((minor_inertia * warping_constant) ** 0.5 / major_section_modulus) ** 0.5


def _flexural_flange_local_buckling_non_compact(
    plastic_moment: Quantity,
    yield_stress: Quantity,
    section_modulus: Quantity,
    flange_ratio: float,
    compact_limit_ratio: float,
    slender_limit_ratio: float,
) -> Quantity:
    ratio = (flange_ratio - slender_limit_ratio) / (
        compact_limit_ratio - slender_limit_ratio
    )
    return (
        plastic_moment - (plastic_moment - 0.7 * yield_stress * section_modulus) * ratio
    )


def _flexural_and_axial_compression_h1_1_validity(
    minor_axis_elastic_section_modulus: Quantity,
    minor_axis_compression_flange_elastic_section_modulus: Quantity,
) -> bool:
    ratio = ratio_simplify(
        minor_axis_compression_flange_elastic_section_modulus,
        minor_axis_elastic_section_modulus,
    )
    return 0.1 <= ratio <= 0.9


def _axial_strength_ratio(required_axial_strength, available_axial_strength):
    return ratio_simplify(required_axial_strength, available_axial_strength)


def _flexural_and_axial_compression_h1_1_criteria(
    required_axial_strength: Quantity,
    available_axial_strength: Quantity,
    required_major_axis_flexural_strength: Quantity,
    available_major_axis_flexural_strength: Quantity,
    required_minor_axis_flexural_strength: Quantity,
    available_minor_axis_flexural_strength: Quantity,
) -> float:
    # required_values can have a sign but only magnitude of loads is relevant, therefore the abs() call)
    axial_strength_ratio = abs(
        ratio_simplify(required_axial_strength, available_axial_strength)
    )
    minor_axis_ratio = abs(
        ratio_simplify(
            required_minor_axis_flexural_strength,
            available_minor_axis_flexural_strength,
        )
    )
    major_axis_ratio = abs(
        ratio_simplify(
            required_major_axis_flexural_strength,
            available_major_axis_flexural_strength,
        )
    )
    factor = 8.0 / 9.0 if axial_strength_ratio >= 0.2 else 1.0
    denominator = 1.0 if axial_strength_ratio >= 0.2 else 2.0
    return axial_strength_ratio / denominator + factor * (
        minor_axis_ratio + major_axis_ratio
    )


def _flexural_and_axial_compression_h1_3_validity(
    required_minor_axis_flexural_strength: Quantity,
    available_minor_axis_flexural_strength: Quantity,
) -> bool:
    ratio = ratio_simplify(
        required_minor_axis_flexural_strength, available_minor_axis_flexural_strength
    )
    return ratio >= 0.05


def _flexural_and_axial_compression_h1_3_criteria(
    required_axial_strength: Quantity,
    available_axial_strength: Quantity,
    required_major_axis_flexural_strength: Quantity,
    available_major_axis_flexural_strength: Quantity,
    mod_factor: float,
) -> float:
    axial_strength_ratio = ratio_simplify(
        required_axial_strength, available_axial_strength
    )
    flexural_strength_ratio = ratio_simplify(
        required_major_axis_flexural_strength, available_major_axis_flexural_strength
    )
    return (
        axial_strength_ratio * (1.5 + 0.5 * available_axial_strength)
        + (flexural_strength_ratio / mod_factor) ** 2
    )


def _minimum_allowed_strength(strengths: Collection[Quantity]):
    strengths = filter(lambda x: x, strengths)
    return min(strengths)


def doubly_symmetric_i_torsional_constant(
    flange_width: Quantity,
    total_height: Quantity,
    flange_thickness: Quantity,
    web_thickness: Quantity,
) -> Quantity:
    return (
        2 * flange_width * flange_thickness**3
        + (total_height - flange_thickness) * web_thickness**3
    ) / 3


def _nominal_shear_strength(
    yield_stress: Quantity, web_area: Quantity, web_shear_coefficient: float = 1.0
):
    return 0.6 * yield_stress * web_area * web_shear_coefficient


def _web_shear_coefficient_limit(
    factor: float,
    web_shear_buckling_coefficient: float,
    modulus_linear: Quantity,
    yield_stress: Quantity,
) -> float:
    return (
        factor
        * ratio_simplify(web_shear_buckling_coefficient * modulus_linear, yield_stress)
        ** 0.5
    )


def _web_shear_coefficient_ii(
    shear_buckling_coefficient: float,
    modulus_linear: Quantity,
    yield_stress: Quantity,
    web_slenderness: float,
):
    return (
        1.10
        * (shear_buckling_coefficient * modulus_linear / yield_stress) ** 0.5
        / web_slenderness
    )


def web_shear_coefficient_iii(
    shear_buckling_coefficient: float,
    modulus_linear: Quantity,
    yield_stress: Quantity,
    web_slenderness: float,
):
    return (
        1.51
        * shear_buckling_coefficient
        * modulus_linear
        / (yield_stress * web_slenderness**2)
    )


def web_height(total_height: Quantity, flange_thickness: Quantity):
    return total_height - 2 * flange_thickness


def _total_height(web_height: Quantity, flange_thickness: Quantity):
    return web_height + 2 * flange_thickness


def _channel_area(
    web_height: Quantity,
    web_thickness: Quantity,
    flange_width: Quantity,
    flange_thickness: Quantity,
):
    return web_height * web_thickness + 2 * flange_thickness * flange_width
