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
    limiting_length_lateral_torsional_buckling, limiting_length_yield, flexural_lateral_torsional_buckling_strength,
    flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c,
    flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric,
    flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b,
)
from structure_scripts.section_properties import Section

if TYPE_CHECKING:
    from structure_scripts.sections import DoublySymmetricI


@dataclass
class MajorAxisFlexurePlasticYielding:
    """F2.1 see page 103"""

    section: Section

    @cached_property
    def nominal_strength(self):
        return flexural_major_axis_yield_strength(
            yield_stress=self.section.material.yield_stress,
            section_modulus=self.section.area_properties.major_axis_plastic_section_modulus,
        )

    @cached_property
    def detailed_results(self):
        return {NOMINAL_STRENGTH: self.nominal_strength}


@dataclass
class MinorAxisFlexurePlasticYielding:
    """F6.1 see page 111"""

    section: Section

    @cached_property
    def nominal_strength(self):
        return flexural_minor_axis_yield_strength(
            yield_stress=self.section.material.yield_stress,
            plastic_section_modulus=self.section.area_properties.minor_axis_plastic_section_modulus,
            elastic_section_modulus=self.section.area_properties.minor_axis_elastic_section_modulus,
        )

    @cached_property
    def detailed_results(self):
        return {NOMINAL_STRENGTH: self.nominal_strength}


@dataclass
class LateralTorsionalBuckling(ABC):
    """F2.2 see page 193"""

    section: Union["DoublySymmetricI", ]
    modification_factor: float
    length_major_axis: Quantity

    @property
    @abstractmethod
    def coefficient_c(self) -> float:
        pass

    @cached_property
    def effective_radius_of_gyration(self):
        """F2-7 page 104"""
        return effective_radius_of_gyration(
            major_section_modulus=self.section.area_properties.major_axis_elastic_section_modulus,
            minor_inertia=self.section.area_properties.minor_axis_inertia,
            warping_constant=self.section.area_properties.warping_constant,
        )

    @cached_property
    def limit_length_torsional_buckling(self):
        return limiting_length_lateral_torsional_buckling(
            modulus=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
            section_modulus=self.section.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.section.area_properties.polar_inertia,
            effective_radius_of_gyration=self.effective_radius_of_gyration,
            distance_between_centroids=self.section.dimensions.distance_between_centroids,
            coefficient_c=self.coefficient_c,
        )

    @cached_property
    def limit_length_yield(self):
        return limiting_length_yield(
            modulus=self.section.material.modulus_linear,
            radius_of_gyration=self.section.area_properties.minor_axis_radius_of_gyration,
            yield_stress=self.section.material.yield_stress,
        )

    @cached_property
    def strength_lateral_torsion_compact_case_b(self) -> Quantity:
        return flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.length_major_axis,
            limiting_length_torsional_buckling=self.limit_length_torsional_buckling,
            limiting_length_yield=self.limit_length_yield,
            mod_factor=self.modification_factor,
            plastic_moment=self.section.area_properties.major_axis_plastic_section_modulus,
            section_modulus=self.section.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.section.material.yield_stress
        )

    @cached_property
    def critical_stress_lateral_torsional_buckling(self) -> Quantity:
        return flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=self.modification_factor,
            length_between_braces=self.length_major_axis,
            modulus=self.section.material.modulus_linear,
            coefficient_c=self.coefficient_c,
            distance_between_flange_centroids=self.section.dimensions.distance_between_centroids,
            effective_radius_of_gyration=self.effective_radius_of_gyration,
            section_modulus=self.section.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.section.area_properties.polar_inertia
        )

    @cached_property
    def strength_lateral_torsion_compact_case_c(self) -> Quantity:
        return flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.section.area_properties.major_axis_plastic_section_modulus,
            section_modulus=self.section.area_properties.major_axis_elastic_section_modulus,
            critical_stress=self.critical_stress_lateral_torsional_buckling,
        )

    @cached_property
    def nominal_strength(self) -> Optional[Quantity]:
        return flexural_lateral_torsional_buckling_strength(
            case_b=self.strength_lateral_torsion_compact_case_b,
            case_c=self.strength_lateral_torsion_compact_case_c,
            length_between_braces=self.length_major_axis,
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