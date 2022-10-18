from dataclasses import dataclass
from typing import Protocol

from quantities import Quantity

from structure_scripts.shared.helpers import radius_of_gyration


class AxisBending(Protocol):
    inertia: Quantity
    elastic_section_modulus: Quantity
    plastic_section_modulus: Quantity
    radius_of_gyration: Quantity


@dataclass
class AxisBendingData:
    inertia: Quantity
    elastic_section_modulus: Quantity
    plastic_section_modulus: Quantity
    radius_of_gyration: Quantity


class Torsion(Protocol):
    inertia: Quantity
    radius_of_gyration: Quantity


@dataclass
class TorsionData:
    inertia: Quantity
    radius_of_gyration: Quantity


class AreaProperties(Protocol):
    area: Quantity
    major_axis: AxisBending
    minor_axis: AxisBending
    torsion: Torsion
    warping_constant: Quantity


class DirectInputAreaProperties(AreaProperties):
    def __init__(
            self,
            area: Quantity,
            major_axis_inertia: Quantity,
            major_axis_elastic_section_modulus: Quantity,
            minor_axis_inertia: Quantity,
            minor_axis_elastic_section_modulus: Quantity,
            polar_inertia: Quantity,
            major_axis_plastic_section_modulus: Quantity | None = None,
            minor_axis_plastic_section_modulus: Quantity | None = None,
            major_axis_radius_of_gyration: Quantity | None = None,
            minor_axis_radius_of_gyration: Quantity | None = None,
            torsional_radius_of_gyration: Quantity | None = None,
            warping_constant: Quantity | None = None,
    ):
        if not major_axis_plastic_section_modulus:
            major_axis_plastic_section_modulus = major_axis_elastic_section_modulus
        if not minor_axis_plastic_section_modulus:
            minor_axis_plastic_section_modulus = minor_axis_elastic_section_modulus
        if not minor_axis_radius_of_gyration:
            minor_axis_radius_of_gyration = radius_of_gyration(minor_axis_inertia, area)
        if not major_axis_radius_of_gyration:
            major_axis_radius_of_gyration = radius_of_gyration(major_axis_inertia, area)
        if not torsional_radius_of_gyration:
            torsional_radius_of_gyration = radius_of_gyration(polar_inertia, area)
        self.area = area
        self.major_axis = AxisBendingData(
            inertia=major_axis_inertia,
            elastic_section_modulus=major_axis_elastic_section_modulus,
            plastic_section_modulus=major_axis_plastic_section_modulus,
            radius_of_gyration=major_axis_radius_of_gyration
        )
        self.minor_axis = AxisBendingData(
            inertia=minor_axis_inertia,
            elastic_section_modulus=minor_axis_elastic_section_modulus,
            plastic_section_modulus=minor_axis_plastic_section_modulus,
            radius_of_gyration=minor_axis_radius_of_gyration
        )
        self.torsion = TorsionData(
            inertia=polar_inertia,
            radius_of_gyration=torsional_radius_of_gyration
        )
        self.warping_constant = warping_constant





