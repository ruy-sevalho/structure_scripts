from dataclasses import dataclass
from functools import cached_property

from structure_scripts.api_rpa.elements import CircularSection
from structure_scripts.api_rpa.helpers import _local_buckling_strength, _representative_elastic_local_buckling_strength


@dataclass
class AxialLoading:
    profile: CircularSection

    @cached_property
    def representative_elastic_local_buckling_strength(self):
        return _representative_elastic_local_buckling_strength(
            elastic_critical_buckling_coefficient=0.3,
            modulus=self.profile.material.modulus_linear,
            outside_diameter=self.profile.geometry.outside_diameter,
            wall_thickness=self.profile.geometry.wall_thickness
        )

    @cached_property
    def local_buckling_strength(self):
        return _local_buckling_strength(
            yield_strength=self.profile.material.yield_stress,
            representative_elastic_local_buckling_strength=self.representative_elastic_local_buckling_strength
        )