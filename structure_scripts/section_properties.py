from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from quantities import Quantity, m

from structure_scripts.helpers import radius_of_gyration
from structure_scripts.materials import IsotropicMaterial


@dataclass(frozen=True)
class AreaProperties:
    A: Quantity
    Ix: Quantity
    Iy: Quantity
    J: Quantity
    Sx: Quantity
    Sy: Quantity
    Zx: Quantity
    Zy: Quantity
    rx: Quantity
    ry: Quantity
    ro: Quantity
    xs: Quantity
    ys: Quantity
    Cw: Quantity


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
        A=area,
        Cw=warping_constant,
        Ix=major_axis_inertia,
        Iy=minor_axis_inertia,
        J=torsional_constant,
        Sx=major_axis_elastic_section_modulus,
        Sy=minor_axis_elastic_section_modulus,
        Zx=major_axis_plastic_section_modulus
        or major_axis_elastic_section_modulus,
        Zy=minor_axis_plastic_section_modulus
        or minor_axis_elastic_section_modulus,
        rx=major_axis_radius_of_gyration
        or radius_of_gyration(
            moment_of_inertia=major_axis_inertia, gross_section_area=area
        ),
        ry=minor_axis_radius_of_gyration
        or radius_of_gyration(
            moment_of_inertia=minor_axis_inertia, gross_section_area=area
        ),
        ro=polar_radius_of_gyration
        or radius_of_gyration(
            moment_of_inertia=torsional_constant, gross_section_area=area
        ),
        xs=major_axis_shear_centroid or Quantity(0, m),
        ys=minor_axis_shear_centroid or Quantity(0, m),
    )


class Section(Protocol):
    material: IsotropicMaterial
    area_properties: AreaProperties


class ConstructionType(str, Enum):
    ROLLED = "ROLLED"
    BUILT_UP = "BUILT_UP"
