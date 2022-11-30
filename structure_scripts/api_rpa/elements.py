import math
from dataclasses import dataclass
from functools import cached_property

from quantities import Quantity

from structure_scripts.helpers import (
    _circular_section_radius_of_gyration,
    _circular_section_moment_of_inertia,
    circular_section_polar_moment_of_inertia,
    section_modulus,
)
from structure_scripts.materials import IsotropicMaterial


@dataclass
class CircularSectionGeometry:
    outer_diameter: Quantity
    wall_thickness: Quantity

    @cached_property
    def inner_diameter(self):
        return self.outer_diameter - 2 * self.wall_thickness

    @cached_property
    def diameter(self):
        return (self.outer_diameter + self.inner_diameter) / 2

    @cached_property
    def radius_of_gyration(self):
        return _circular_section_radius_of_gyration(
            outer_diameter=self.outer_diameter,
            inner_diameter=self.inner_diameter,
        )

    @cached_property
    def moment_of_inertia(self):
        return _circular_section_moment_of_inertia(
            outer_diameter=self.outer_diameter,
            inner_diameter=self.inner_diameter,
        )

    @cached_property
    def torsional_constant(self):
        return circular_section_polar_moment_of_inertia(
            outer_diameter=self.outer_diameter,
            inner_diameter=self.inner_diameter,
        )

    @cached_property
    def section_modulus(self):
        return section_modulus(
            inertia=self.moment_of_inertia,
            max_distance_to_neutral_axis=self.outer_diameter / 2,
        )

    @cached_property
    def area(self):
        return (
            math.pi * (self.outer_diameter**2 - self.inner_diameter**2) / 4
        )


@dataclass
class CircularSection:
    geometry: CircularSectionGeometry
    material: IsotropicMaterial
