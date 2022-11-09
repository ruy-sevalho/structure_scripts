from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING
from functools import cached_property
from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    # SafetyFactor,
    # AllowableStrengthDesign,
    # CriteriaAdaptor,
    NOMINAL_STRENGTH,
    DesignType,
)
from structure_scripts.aisc_360_10.helpers import (
    elastic_flexural_buckling_stress,
    critical_compression_stress_buckling_default,
    _nominal_compressive_strength,
)

from structure_scripts.section_properties import Section
from structure_scripts.helpers import member_slenderness_ratio, Axis

if TYPE_CHECKING:
    pass

FLEXURAL_BUCKLING_MAJOR_AXIS_STRENGTH = "flexural_buckling_major_axis_strength"
FLEXURAL_BUCKLING_MINOR_AXIS_STRENGTH = "flexural_buckling_major_axis_strength"
TORSIONAL_BUCKLING_STRENGTH = "torsional_buckling_strength"
ELASTIC_BUCKLING_STRESS = "elastic_buckling_stress"
BUCKLING_CRITICAL_STRESS = "buckling_critical_stress"

# @dataclass
# class CompressionFlexuralBucklingCompact(Criteria):
#     slenderness: float
#     section_area: Quantity
#     material: IsotropicMaterial
#     member_slenderness_limit: float
#     safety_factor: SafetyFactor = AllowableStrengthDesign()

#     @cached_property
#     def elastic_flexural_buckling_stress(self):
#         return elastic_flexural_buckling_stress(
#             modulus_linear=self.material.modulus_linear,
#             member_slenderness_ratio=self.slenderness,
#         )

#     @cached_property
#     def flexural_buckling_critical_stress(self):
#         return critical_compression_stress_buckling_default(
#             member_slenderness=self.slenderness,
#             elastic_buckling_stress=self.elastic_flexural_buckling_stress,
#             member_slenderness_limit=self.member_slenderness_limit,
#             yield_stress=self.material.yield_stress,
#         )

#     @cached_property
#     def nominal_strength(self) -> Quantity:
#         return _nominal_compressive_strength(
#             self.flexural_buckling_critical_stress, sectional_area=self.section_area
#         )


# @dataclass
# class CompressionTorsionalBuckling(Criteria):
#     slenderness: float
#     section_area: Quantity
#     modulus_linear: Quantity
#     yield_stress: Quantity
#     member_slenderness_limit: float
#     safety_factor: SafetyFactor = AllowableStrengthDesign()

#     @cached_property
#     def elastic_flexural_buckling_stress(self):
#         return elastic_flexural_buckling_stress(
#             modulus_linear=self.modulus_linear,
#             member_slenderness_ratio=self.slenderness,
#         )

#     @cached_property
#     def flexural_buckling_critical_stress(self):
#         return critical_compression_stress_buckling_default(
#             member_slenderness=self.slenderness,
#             elastic_buckling_stress=self.elastic_flexural_buckling_stress,
#             member_slenderness_limit=self.member_slenderness_limit,
#             yield_stress=self.yield_stress,
#         )

#     @cached_property
#     def nominal_strength(self) -> Quantity:
#         return _nominal_compressive_strength(
#             self.flexural_buckling_critical_stress, sectional_area=self.section_area
#         )

#
# class BucklingStrengthGeneralCalculation(Strength, Protocol):
#     critical_stress: Quantity
#
#
# class BucklingStrengthEulerCalculation(
#     BucklingStrengthGeneralCalculation, Protocol
# ):
#     elastic_buckling_stress: Quantity


@dataclass
class BeamCompression:
    length_major_axis: Quantity
    factor_k_major_axis: float = 1.0
    length_minor_axis: Quantity = None
    factor_k_minor_axis: float = 1.0
    length_torsion: Quantity = None
    factor_k_torsion: float = 1.0
    design_type: DesignType = DesignType.ASD


@dataclass(frozen=True)
class BucklingStrengthMixin(ABC):
    section: Section

    @cached_property
    def critical_stress(self):
        return critical_compression_stress_buckling_default(
            elastic_buckling_stress=self.elastic_buckling_stress,
            yield_stress=self.section.material.yield_stress,
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.critical_stress,
            sectional_area=self.section.area_properties.area,
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
    section: Section
    length: Quantity
    factor_k: float
    axis: Axis

    @cached_property
    def radius_of_gyration(self):
        table = {
            Axis.MAJOR: self.section.area_properties.major_axis_radius_of_gyration,
            Axis.MINOR: self.section.area_properties.minor_axis_radius_of_gyration,
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
            modulus_linear=self.section.material.modulus_linear,
            member_slenderness_ratio=self.beam_slenderness,
        )
