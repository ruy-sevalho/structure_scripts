from dataclasses import dataclass
from functools import cached_property
from typing import Union, TYPE_CHECKING, Optional
from abc import ABC, abstractmethod

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import NOMINAL_STRENGTH
from structure_scripts.aisc_360_10.helpers import (
    flexural_major_axis_yield_strength,
    flexural_minor_axis_yield_strength,
    effective_radius_of_gyration,
    limiting_length_lateral_torsional_buckling,
    limiting_length_yield,
    flexural_lateral_torsional_buckling_strength,
    flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c,
    flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric,
    flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b, kc_coefficient,
)
from structure_scripts.helpers import Axis
from structure_scripts.section import ProfileFlangeWeb, Profile, SectionType
from structure_scripts.section_properties import Section

if TYPE_CHECKING:
    from structure_scripts.sections_from_dimensions import DoublySymmetricI
    from structure_scripts.aisc_360_10.i_profile import (
        DoublySymmetricIAISC36010,
    )


@dataclass(frozen=True)
class BeamFlexure:
    length: Quantity
    lateral_torsional_buckling_modification_factor: float = 1


@dataclass(frozen=True)
class MajorAxisFlexurePlasticYielding:
    """F2.1 see page 103"""

    profile: Profile

    @cached_property
    def nominal_strength(self):
        return flexural_major_axis_yield_strength(
            yield_stress=self.profile.material.yield_stress,
            section_modulus=self.profile.section.Zx,
        )

    @cached_property
    def detailed_results(self):
        return {NOMINAL_STRENGTH: self.nominal_strength}


@dataclass
class MinorAxisFlexurePlasticYielding:
    """F6.1 see page 111"""

    profile: Profile

    @cached_property
    def nominal_strength(self):
        return flexural_minor_axis_yield_strength(
            yield_stress=self.profile.material.yield_stress,
            plastic_section_modulus=self.profile.section.Zy,
            elastic_section_modulus=self.profile.section.Sy,
        )

    @cached_property
    def detailed_results(self):
        return {NOMINAL_STRENGTH: self.nominal_strength}


@dataclass(frozen=True)
class LateralTorsionalBuckling(ABC):
    """F2 page 103"""

    profile: ProfileFlangeWeb
    modification_factor: float
    length: Quantity

    @property
    @abstractmethod
    def coefficient_c(self) -> float:
        pass

    @cached_property
    def effective_radius_of_gyration(self):
        """F2-7 page 104"""
        return effective_radius_of_gyration(
            major_section_modulus=self.profile.section.Sx,
            minor_inertia=self.profile.section.Iy,
            warping_constant=self.profile.section.Cw,
        )

    @cached_property
    def limit_length_torsional_buckling(self):
        return limiting_length_lateral_torsional_buckling(
            modulus=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress,
            section_modulus=self.profile.section.Sx,
            torsional_constant=self.profile.section.J,
            effective_radius_of_gyration=self.profile.section.rts,
            distance_between_centroids=self.profile.section.ho,
            coefficient_c=self.coefficient_c,
        )

    @cached_property
    def limit_length_yield(self):
        return limiting_length_yield(
            modulus=self.profile.material.modulus_linear,
            radius_of_gyration=self.profile.section.ry,
            yield_stress=self.profile.material.yield_stress,
        )

    @cached_property
    def strength_lateral_torsion_compact_case_b(self) -> Quantity:
        """F2-1 page 103"""
        return flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.length,
            limiting_length_torsional_buckling=self.limit_length_torsional_buckling,
            limiting_length_yield=self.limit_length_yield,
            mod_factor=self.modification_factor,
            plastic_moment=self.profile.section.Zx
            * self.profile.material.yield_stress,
            section_modulus=self.profile.section.Sx,
            yield_stress=self.profile.material.yield_stress,
        )

    @cached_property
    def critical_stress_lateral_torsional_buckling(self) -> Quantity:
        return flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=self.modification_factor,
            length_between_braces=self.length,
            modulus=self.profile.material.modulus_linear,
            coefficient_c=self.coefficient_c,
            distance_between_flange_centroids=self.profile.section.ho,
            effective_radius_of_gyration=self.effective_radius_of_gyration,
            section_modulus=self.profile.section.Sx,
            torsional_constant=self.profile.section.J,
        )

    @cached_property
    def strength_lateral_torsion_compact_case_c(self) -> Quantity:
        return flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.profile.section.Zx,
            section_modulus=self.profile.section.Sx,
            critical_stress=self.critical_stress_lateral_torsional_buckling,
        )

    @cached_property
    def nominal_strength(self) -> Optional[Quantity]:
        return flexural_lateral_torsional_buckling_strength(
            case_b=self.strength_lateral_torsion_compact_case_b,
            case_c=self.strength_lateral_torsion_compact_case_c,
            length_between_braces=self.length,
            limiting_length_yield=self.limit_length_yield,
            limiting_length_torsional_buckling=self.limit_length_torsional_buckling,
        )

    @cached_property
    def detailed_results(self):
        return {
            "limit_length_yield": self.limit_length_yield,
            "limit_length_torsional_buckling": self.limit_length_torsional_buckling,
            NOMINAL_STRENGTH: self.nominal_strength,
        }


@dataclass(frozen=True)
class NonCompactFlangeLocalBuckling:
    """
    lambda_p:  limiting slenderness for a compact flange
    lambda_r:  limiting slenderness for a noncompact flange
    lambda: flange slenderness ratio bf_2tf
    """
    profile: ProfileFlangeWeb
    axis: Axis

    @cached_property
    def lambda_p(self):
        table = {
            Axis.MAJOR: self.profile.slenderness_calc_memory.flexure_major_axis.flange.compact_non_compact_limit,
            Axis.MINOR: self.profile.slenderness_calc_memory.flexure_minor_axis.flange.compact_non_compact_limit
        }
        return table[self.axis]

    @cached_property
    def lambda_r(self):
        table = {
            Axis.MAJOR: self.profile.slenderness_calc_memory.flexure_major_axis.flange.non_compact_slender_limit,
            Axis.MINOR: self.profile.slenderness_calc_memory.flexure_minor_axis.flange.non_compact_slender_limit
        }
        return table[self.axis]

    @cached_property
    def nominal_strength(self) -> Quantity:
        table = {
            Axis.MAJOR: (self.profile.flex_yield_major_axis.nominal_strength, self.profile.section.Sx),
            Axis.MINOR: (self.profile.flex_yield_minor_axis.nominal_strength, self.profile.section.Sy)
        }
        mp, S = table[self.axis]
        factor1 = (mp - 0.7*self.profile.material.yield_stress*S)
        factor2 = (self.profile.section.bf_2tf - self.lambda_p)/ (self.lambda_r - self.lambda_p)
        res = mp - factor1*factor2
        return mp - factor1*factor2

    @cached_property
    def detailed_results(self):
        return {
            NOMINAL_STRENGTH: self.nominal_strength
        }


@dataclass(frozen=True)
class SlenderFlangeLocalBuckingMajorAxis:
    profile: ProfileFlangeWeb

    @cached_property
    def nominal_strength(self) -> Quantity:
        return 0.9 * self.profile.material.modulus_linear * self.kc * self.profile.section / self.profile.section.bf_2tf**2

    @cached_property
    def kc(self):
        return kc_coefficient(h_tw=self.profile.section.h_tw)

    @cached_property
    def detailed_results(self):
        return {
            "kc_coefficient": self.kc,
            NOMINAL_STRENGTH: self.nominal_strength
        }


@dataclass(frozen=True)
class SlenderFlangeLocalBuckingMinorAxis:
    profile: ProfileFlangeWeb

    @cached_property
    def critical_stress(self) -> Quantity:
        table = {
            SectionType.C: self.profile.section.b_t,
            SectionType.W: self.profile.section.bf_2tf,
            SectionType.M: self.profile.section.bf_2tf,
            SectionType.HP: self.profile.section.bf_2tf,
        }
        return 0.69 * self.profile.material.modulus_linear / table[self.profile.section.type]

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self.critical_stress * self.profile.section.Sy

    @cached_property
    def detailed_results(self):
        return {
            "critical_stress": self.critical_stress,
            NOMINAL_STRENGTH: self.nominal_strength
        }