import math

from quantities import Quantity, dimensionless


def ratio_simplify(q1: Quantity, q2: Quantity) -> float:
    r: Quantity = (q1 / q2).simplified
    if not r.units == dimensionless:
        raise ValueError("q1/q2 is not dimensionless")
    return r.magnitude


def member_slenderness_ratio(factor_k: float, unbraced_length: Quantity, radius_of_gyration: Quantity) -> float:
    n = ratio_simplify(unbraced_length, radius_of_gyration)
    return factor_k * n


def _circular_section_radius_of_gyration(outer_diameter: Quantity, inner_diameter: Quantity):
    return (outer_diameter ** 2 + inner_diameter ** 2) ** 0.5 / 4


def _circular_section_moment_of_inertia(outer_diameter: Quantity, inner_diameter: Quantity):
    return (outer_diameter ** 4 - inner_diameter ** 4) * math.pi / 4


def circular_section_polar_moment_of_inertia(outer_diameter: Quantity, inner_diameter: Quantity):
    return math.pi * (outer_diameter**4 - inner_diameter**4)/32


def same_units_simplify(q1: Quantity, q2: Quantity):
    q1 = q1.simplified
    q2 = q2.simplified
    if not q1.units == q2.units:
        raise ValueError("q1 and q2 don't have the same units")
    return q1, q2


def section_modulus(inertia: Quantity, max_distance_to_neutral_axis: Quantity) -> Quantity:
    return inertia / max_distance_to_neutral_axis
