from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from quantities import Quantity, m

from structure_scripts.helpers import radius_of_gyration
from structure_scripts.materials import IsotropicMaterial


@dataclass(frozen=True)
class AreaProperties:
    area: Quantity
    major_axis_inertia: Quantity
    minor_axis_inertia: Quantity
    torsional_constant: Quantity
    major_axis_elastic_section_modulus: Quantity
    minor_axis_elastic_section_modulus: Quantity
    major_axis_plastic_section_modulus: Quantity
    minor_axis_plastic_section_modulus: Quantity
    major_axis_radius_of_gyration: Quantity
    minor_axis_radius_of_gyration: Quantity
    polar_radius_of_gyration: Quantity
    major_axis_shear_centroid: Quantity
    minor_axis_shear_centroid: Quantity
    warping_constant: Quantity


def section_geo_properties(
    area: Quantity,
    warping_constant: Quantity,
    major_axis_inertia: Quantity,
    major_axis_elastic_section_modulus: Quantity,
    minor_axis_inertia: Quantity,
    minor_axis_elastic_section_modulus: Quantity,
    torsional_constant: Quantity,
    major_axis_plastic_section_modulus: Quantity | None = None,
    minor_axis_plastic_section_modulus: Quantity | None = None,
    major_axis_radius_of_gyration: Quantity | None = None,
    minor_axis_radius_of_gyration: Quantity | None = None,
    polar_radius_of_gyration: Quantity | None = None,
    major_axis_shear_centroid: Quantity | None = None,
    minor_axis_shear_centroid: Quantity | None = None,
):
    return AreaProperties(
        area=area,
        warping_constant=warping_constant,
        major_axis_inertia=major_axis_inertia,
        minor_axis_inertia=minor_axis_inertia,
        torsional_constant=torsional_constant,
        major_axis_elastic_section_modulus=major_axis_elastic_section_modulus,
        minor_axis_elastic_section_modulus=minor_axis_elastic_section_modulus,
        major_axis_plastic_section_modulus=major_axis_plastic_section_modulus
        or major_axis_elastic_section_modulus,
        minor_axis_plastic_section_modulus=minor_axis_plastic_section_modulus
        or minor_axis_elastic_section_modulus,
        major_axis_radius_of_gyration=major_axis_radius_of_gyration
        or radius_of_gyration(
            moment_of_inertia=major_axis_inertia, gross_section_area=area
        ),
        minor_axis_radius_of_gyration=minor_axis_radius_of_gyration
        or radius_of_gyration(
            moment_of_inertia=minor_axis_inertia, gross_section_area=area
        ),
        polar_radius_of_gyration=polar_radius_of_gyration
        or radius_of_gyration(
            moment_of_inertia=torsional_constant, gross_section_area=area
        ),
        major_axis_shear_centroid=major_axis_shear_centroid or Quantity(0, m),
        minor_axis_shear_centroid=minor_axis_shear_centroid or Quantity(0, m),
    )


class Section(Protocol):
    material: IsotropicMaterial
    area_properties: AreaProperties


class ConstructionType(str, Enum):
    ROLLED = "ROLLED"
    BUILT_UP = "BUILT_UP"
