import math

from quantities import Quantity, MPa

from structure_scripts.helpers import ratio_simplify


def _representative_elastic_local_buckling_strength(
    elastic_critical_buckling_coefficient,
    modulus: Quantity,
    outside_diameter: Quantity,
    wall_thickness: Quantity,
) -> Quantity:
    return (
        2
        * elastic_critical_buckling_coefficient
        * modulus
        * wall_thickness
        / outside_diameter
    )


def _local_buckling_strength(
    yield_strength: Quantity,
    representative_elastic_local_buckling_strength: Quantity,
):
    if yield_strength / representative_elastic_local_buckling_strength <= 0.17:
        strength = yield_strength
    else:
        strength = (
            1.047
            - 0.274
            * yield_strength
            / representative_elastic_local_buckling_strength
        ) * yield_strength
    return strength


def _c_coefficient_collum_buck(
    yield_stress: Quantity, modulus_linear: Quantity
):
    return (
        ratio_simplify(modulus_linear, yield_stress) * 2 * math.pi**2
    ) ** 0.5


def _allowable_compressive_stress_a(
    slenderness: float, c: float, yield_stress: Quantity
):
    return (
        (1 - slenderness**2 / (2 * c**2))
        * yield_stress
        / (
            5.0 / 3.0
            + 3 * slenderness / (8 * c)
            - slenderness**3 / (8 * c**3)
        )
    )


def _allowable_compressive_stress_b(
    slenderness: float, modulus_linear: Quantity
):
    return 12 * math.pi**2 * modulus_linear / (23 * slenderness**2)


def allowable_bending_stress_a(yield_stress: Quantity):
    return 0.75 * yield_stress


def ratio_limit_a(yield_stress: Quantity):
    return (10340 / yield_stress.rescale(MPa)).magnitude


def beam_shear_stress(shear_force: Quantity, cross_area: Quantity):
    return shear_force / (0.5 * cross_area)


def axial_stress(axial_force: Quantity, cross_area: Quantity) -> Quantity:
    return axial_force / cross_area


def bending_stress(bending_moment: Quantity, section_modulus: Quantity):
    return bending_moment / section_modulus


def allowable_shear_stress(yield_stress: Quantity):
    return 0.4 * yield_stress


def max_torsional_shear_stress(
    torsional_moment: Quantity,
    polar_inertia: Quantity,
    outer_diameter: Quantity,
):
    return torsional_moment * outer_diameter / (2 * polar_inertia)


def combined_bending_compression_criteria_a(
    acting_compressive_stress: Quantity,
    acting_bending_stress_x: Quantity,
    acting_bending_stress_y: Quantity,
    elastic_compressive_buckling_stress: Quantity,
    allowable_compressive_stress: Quantity,
    allowable_bending_stress: Quantity,
    modification_coefficient: float,
):
    """Eq 6.20"""
    first_term = ratio_simplify(
        acting_compressive_stress, allowable_compressive_stress
    )
    second_term_numerator = (
        modification_coefficient
        * (acting_bending_stress_x**2 + acting_bending_stress_y**2) ** 0.5
    )
    second_term_denominator = (
        1 - acting_compressive_stress / elastic_compressive_buckling_stress
    ) * allowable_bending_stress
    return first_term + second_term_numerator / second_term_denominator


def combined_bending_compression_criteria_b(
    acting_compressive_stress: Quantity,
    acting_bending_stress_x: Quantity,
    acting_bending_stress_y: Quantity,
    allowable_bending_stress: Quantity,
    yield_stress: Quantity,
):
    """Eq 6.21"""
    first_term = ratio_simplify(
        acting_compressive_stress, (0.6 * yield_stress)
    )
    second_term = ratio_simplify(
        (acting_bending_stress_x**2 + acting_bending_stress_y**2) ** 0.5,
        allowable_bending_stress,
    )
    return first_term + second_term
