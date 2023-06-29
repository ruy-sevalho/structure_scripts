import math
from enum import Enum
from typing import Collection, TYPE_CHECKING

from quantities import Quantity, dimensionless


class Axis(str, Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PRINCIPAL_MINOR = "PRINCIPAL_MINOR"


def ratio_simplify(q1: Quantity, q2: Quantity) -> float:
    r: Quantity = (q1 / q2).simplified
    if not r.units == dimensionless:
        raise ValueError("q1/q2 is not dimensionless")
    return r.magnitude


def member_slenderness_ratio(
    factor_k: float, unbraced_length: Quantity, radius_of_gyration: Quantity
) -> float:
    n = ratio_simplify(unbraced_length, radius_of_gyration)
    return factor_k * n


def _circular_section_radius_of_gyration(
    outer_diameter: Quantity, inner_diameter: Quantity
):
    return (outer_diameter**2 + inner_diameter**2) ** 0.5 / 4


def _circular_section_moment_of_inertia(
    outer_diameter: Quantity, inner_diameter: Quantity
):
    return (outer_diameter**4 - inner_diameter**4) * math.pi / 4


def circular_section_polar_moment_of_inertia(
    outer_diameter: Quantity, inner_diameter: Quantity
):
    return math.pi * (outer_diameter**4 - inner_diameter**4) / 32


def same_units_simplify(q1: Quantity, q2: Quantity, strip_units: bool = False):
    q1 = q1.simplified
    q2 = q2.simplified
    if not q1.units == q2.units:
        raise ValueError(
            f"q1 has {q1.units} units and q2 has {q2.units} units"
        )
    if strip_units:
        return q1.magnitude.item(), q2.magnitude.item()
    return q1, q2


def section_modulus(
    inertia: Quantity, max_distance_to_neutral_axis: Quantity
) -> Quantity:
    return inertia / max_distance_to_neutral_axis


def radius_of_gyration(
    moment_of_inertia: Quantity, gross_section_area: Quantity
):
    return (moment_of_inertia / gross_section_area) ** 0.5


def self_inertia(width: Quantity, height: Quantity) -> Quantity:
    return width * height**3 / 12


def transfer_inertia(
    area: Quantity, center_to_na_distance: Quantity
) -> Quantity:
    return area * center_to_na_distance**2


def rectangle_area(width: Quantity, height: Quantity) -> Quantity:
    return width * height


def areas_centroid(areas: Collection[tuple[Quantity, Quantity]]) -> Quantity:
    summation_weighted_areas = Quantity(0, "mm**3")
    summation_areas = Quantity(0, "mm**2")
    for area in areas:
        summation_weighted_areas = summation_weighted_areas + area[0] * area[1]
        summation_areas = summation_areas + area[0]
    return summation_weighted_areas / summation_areas


def channel_warping_constant(
    web_height_corrected: Quantity,
    web_thickness: Quantity,
    flange_width_corrected: Quantity,
    flange_thickness: Quantity,
    alpha: float,
):
    """pg 7 TORSIONAL SECTION PROPERTIES OF STEEL SHAPES Canadian Institute of Steel Construction, 2002"""
    return (
        web_height_corrected**2
        * flange_width_corrected**3
        * flange_thickness
        * (
            (1 - 3 * alpha) / 6
            + alpha**2
            / 2
            * (
                1
                + (web_height_corrected * web_thickness)
                / (6 * flange_width_corrected * flange_thickness)
            )
        )
    )


def alpha(
    flange_thickness: Quantity,
    flange_width_corrected: Quantity,
    web_height: Quantity,
    web_thickness: Quantity,
) -> float:
    alpha = 1 / (
        2
        + web_height
        * web_thickness
        / (3 * flange_width_corrected * flange_thickness)
    )
    return alpha.simplified.magnitude


def channel_corrected_dimensions(
    flange_thickness, flange_width, web_height, web_thickness
):
    web_height_corrected = web_height - flange_thickness
    flange_width_corrected = flange_width - web_thickness / 2
    return flange_width_corrected, web_height_corrected


def channel_torsional_constant(
    web_height_corrected: Quantity,
    web_thickness: Quantity,
    flange_width_corrected: Quantity,
    flange_thickness: Quantity,
):
    """TORSIONAL SECTION PROPERTIES OF STEEL SHAPES
    Canadian Institute of Steel Construction, 2002
    [9]  (SSRC 1998)
    """
    return (
        2 * flange_width_corrected * flange_thickness**3
        + web_height_corrected * web_thickness**3
    ) / 3


def polar_radius_of_gyration(
    major_axis_shear_centroid: Quantity,
    minor_axis_shear_centroid: Quantity,
    major_axis_inertia: Quantity,
    minor_axis_inertia: Quantity,
    area: Quantity,
) -> Quantity:
    return (
        major_axis_shear_centroid**2
        + minor_axis_shear_centroid**2
        + (minor_axis_inertia + major_axis_inertia) / area
    ) ** 0.5


def minor_axis_plastic_section_modulus_i_channel(
    area: Quantity,
    flange_width: Quantity,
    flange_thickness: Quantity,
    depth: Quantity,
    web_thickness: Quantity,
    web_height: Quantity,
):
    width = flange_width - web_thickness
    sm_a_first_term = flange_thickness * width**2 / 2
    sm_a_second_term = flange_width * depth * web_thickness / 2
    sm_a_third_term = (
        -(depth**2) * web_thickness**2 / (8 * flange_thickness)
    )
    sm_a = sm_a_first_term + sm_a_second_term + sm_a_third_term
    sm_b_factor = 1 / (4 * depth)
    sm_b_first_term = (
        4 * flange_thickness * flange_width**2 * (depth - flange_thickness)
    )
    sm_b_second_term = web_thickness**2 * (
        depth**2 - 4 * flange_thickness**2
    )
    sm_b_third_term = (
        -4 * flange_width * flange_thickness * web_height * web_thickness
    )
    sm_b = sm_b_factor * (sm_b_first_term + sm_b_second_term + sm_b_third_term)
    return sm_a if web_thickness <= area / (2 * depth) else sm_b


# def channel_minor_axis_shear_location(
#
# )
def channel_minor_axis_inertia(
    dimensions: "ChannelDimensions",
) -> tuple[Quantity, Quantity]:
    web_area = dimensions.web_thickness * dimensions.web_height
    web_base_centroid = dimensions.web_thickness / 2
    flange_area = dimensions.flange_width * dimensions.flange_thickness
    flange_base_centroid = dimensions.flange_width / 2
    y_neutral_axis = (
        web_area * web_base_centroid + 2 * flange_area * flange_base_centroid
    ) / (web_area + 2 * flange_area)
    web_self_inertia = self_inertia(
        width=dimensions.web_height, height=dimensions.web_thickness
    )
    web_transfer_inertia = web_area * (y_neutral_axis - web_base_centroid) ** 2
    flange_self_inertia = self_inertia(
        width=dimensions.flange_thickness, height=dimensions.flange_width
    )
    flange_transfer_inertia = (
        flange_area * (y_neutral_axis - flange_base_centroid) ** 2
    )
    return (
        web_transfer_inertia
        + web_self_inertia
        + (flange_self_inertia + flange_transfer_inertia) * 2,
        y_neutral_axis,
    )


def channel_shear_center_delta(
    flange_width_corrected: Quantity,
    alpha: float,
    web_thickness: Quantity,
) -> Quantity:
    """TORSIONAL SECTION PROPERTIES OF STEEL SHAPES
    Canadian Institute of Steel Construction, 2002

    [13] (Galambos 1968, SSRC 1998).
    """
    return flange_width_corrected * alpha - web_thickness / 2


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


def web_height_from_total(
    depth: Quantity, flange_thickness: Quantity
) -> Quantity:
    return depth - 2 * flange_thickness


def _total_height(
    web_height: Quantity, flange_thickness: Quantity
) -> Quantity:
    return web_height + 2 * flange_thickness


def _channel_area(
    web_height: Quantity,
    web_thickness: Quantity,
    flange_width: Quantity,
    flange_thickness: Quantity,
):
    return web_height * web_thickness + 2 * flange_thickness * flange_width


def factor_h(
    major_axis_shear_centroid: Quantity,
    minor_axis_shear_centroid: Quantity,
    polar_radius_of_gyration: Quantity,
) -> float:
    """E4-10"""

    return 1 - ratio_simplify(
        (major_axis_shear_centroid**2 + minor_axis_shear_centroid**2),
        polar_radius_of_gyration**2,
    )
