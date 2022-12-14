from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING
from functools import cached_property
from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    NOMINAL_STRENGTH,
)
from structure_scripts.aisc_360_10.helpers import (
    elastic_flexural_buckling_stress,
    critical_compression_stress_buckling_default,
    _nominal_compressive_strength,
)
from structure_scripts.section import Profile, ProfileFlangeWeb

from structure_scripts.section_properties import Section
from structure_scripts.helpers import member_slenderness_ratio, Axis

if TYPE_CHECKING:
    pass

FLEXURAL_BUCKLING_MAJOR_AXIS_STRENGTH = "flexural_buckling_major_axis_strength"
FLEXURAL_BUCKLING_MINOR_AXIS_STRENGTH = "flexural_buckling_major_axis_strength"
TORSIONAL_BUCKLING_STRENGTH = "torsional_buckling_strength"
ELASTIC_BUCKLING_STRESS = "elastic_buckling_stress"
BUCKLING_CRITICAL_STRESS = "buckling_critical_stress"


@dataclass
class BeamCompression:
    length_major_axis: Quantity
    factor_k_major_axis: float = 1.0
    length_minor_axis: Quantity = None
    factor_k_minor_axis: float = 1.0
    length_torsion: Quantity = None
    factor_k_torsion: float = 1.0


@dataclass(frozen=True)
class BucklingStrengthMixin(ABC):
    profile: Profile

    @cached_property
    def critical_stress(self):
        return critical_compression_stress_buckling_default(
            elastic_buckling_stress=self.elastic_buckling_stress,
            yield_stress=self.profile.material.yield_stress,
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.critical_stress,
            sectional_area=self.profile.section.A,
        )

    @property
    @abstractmethod
    def elastic_buckling_stress(self) -> Quantity:
        pass

    @cached_property
    def detailed_results(self) -> dict[str, Quantity | float]:
        return {
            # ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
            BUCKLING_CRITICAL_STRESS: self.critical_stress,
            NOMINAL_STRENGTH: self.nominal_strength,
        }


@dataclass(frozen=True)
class FlexuralBucklingStrength(BucklingStrengthMixin):
    profile: Profile
    length: Quantity
    factor_k: float
    axis: Axis

    @cached_property
    def radius_of_gyration(self):
        table = {
            Axis.MAJOR: self.profile.section.rx,
            Axis.MINOR: self.profile.section.ry,
        }
        return table[self.axis]

    @cached_property
    def beam_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k,
            radius_of_gyration=self.radius_of_gyration,
            unbraced_length=self.length,
        )

    @cached_property
    def detailed_results(self) -> dict[str, Quantity | float]:
        return {
            ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
            **super().detailed_results,
        }

    @cached_property
    def elastic_buckling_stress(self):
        return elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.beam_slenderness,
        )



