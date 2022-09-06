from dataclasses import dataclass
from functools import cached_property

from quantities import Quantity, GPa, MPa, mm

from structure_scripts.shared.materials import IsoTropicMaterial, Material
from structure_scripts.api_rpa_lrfd.helpers import _representative_elastic_local_buckling_strength, \
    _local_buckling_strength


@dataclass
class CircularSectionGeometry:
    outside_diameter: Quantity
    wall_thickness: Quantity

    @cached_property
    def inner_diameter(self):
        return self.outside_diameter - self.wall_thickness


@dataclass
class CircularSection:
    geometry: CircularSectionGeometry
    material: Material

    @cached_property
    def representative_elastic_local_buckling_strength(self):
        return _representative_elastic_local_buckling_strength(
            elastic_critical_buckling_coefficient=0.3,
            modulus=self.material.modulus_linear,
            outside_diameter=self.geometry.outside_diameter,
            wall_thickness=self.geometry.wall_thickness
        )

    @cached_property
    def local_buckling_strength(self):
        return _local_buckling_strength(
            yield_strength=self.material.yield_stress,
            representative_elastic_local_buckling_strength=self.representative_elastic_local_buckling_strength
        )


if __name__ == "__main__":
    steel = IsoTropicMaterial(
        modulus_linear=200 * GPa,
        modulus_shear=77 * GPa,
        poisson_ratio=0.3,
        yield_stress=355 * MPa
    )
    p4geo = CircularSectionGeometry(
        outside_diameter=114.4 * mm,
        wall_thickness=6.02 * mm
    )
    p4 = CircularSection(geometry=p4geo, material=steel)
    print(p4.local_buckling_strength.rescale(MPa))
