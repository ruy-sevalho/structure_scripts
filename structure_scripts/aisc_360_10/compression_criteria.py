from dataclasses import dataclass
from functools import partial
from typing import Literal

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    Criteria,
    SafetyFactor,
    AllowableStrengthDesign,
    CriteriaAdaptor,
)
from structure_scripts.aisc_360_10.beams import (
    BucklingParam,
    BeamAnalysis,
    BeamGlobalData,
)
from structure_scripts.aisc_360_10.helpers import (
    elastic_flexural_buckling_stress,
    _member_slenderness_limit,
    critical_compression_stress_buckling_default,
    _nominal_compressive_strength,
)
from structure_scripts.aisc_360_10.sections import Section
from structure_scripts.shared.helpers import member_slenderness_ratio, Axis
from structure_scripts.shared.materials import IsotropicMaterial

FLEXURAL_BUCKLING_MAJOR = "flexural_buckling_major_axis"
FLEXURAL_BUCKLING_MINOR = "flexural_buckling_major_axis"
TORSIONAL_BUCKLING = "torsional_buckling"


# @dataclass
# class CompressionFlexuralBucklingCompact(Criteria):
#     slenderness: float
#     section_area: Quantity
#     material: IsotropicMaterial
#     member_slenderness_limit: float
#     safety_factor: SafetyFactor = AllowableStrengthDesign()

#     @property
#     def elastic_flexural_buckling_stress(self):
#         return elastic_flexural_buckling_stress(
#             modulus_linear=self.material.modulus_linear,
#             member_slenderness_ratio=self.slenderness,
#         )

#     @property
#     def flexural_buckling_critical_stress(self):
#         return critical_compression_stress_buckling_default(
#             member_slenderness=self.slenderness,
#             elastic_buckling_stress=self.elastic_flexural_buckling_stress,
#             member_slenderness_limit=self.member_slenderness_limit,
#             yield_stress=self.material.yield_stress,
#         )

#     @property
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

#     @property
#     def elastic_flexural_buckling_stress(self):
#         return elastic_flexural_buckling_stress(
#             modulus_linear=self.modulus_linear,
#             member_slenderness_ratio=self.slenderness,
#         )

#     @property
#     def flexural_buckling_critical_stress(self):
#         return critical_compression_stress_buckling_default(
#             member_slenderness=self.slenderness,
#             elastic_buckling_stress=self.elastic_flexural_buckling_stress,
#             member_slenderness_limit=self.member_slenderness_limit,
#             yield_stress=self.yield_stress,
#         )

#     @property
#     def nominal_strength(self) -> Quantity:
#         return _nominal_compressive_strength(
#             self.flexural_buckling_critical_stress, sectional_area=self.section_area
#         )


@dataclass
class BucklingStrength(Criteria):
    elastic_buckling_stress: Quantity
    slenderness: float
    section_area: Quantity
    yield_stress: Quantity
    # member_slenderness_limit: float

    @property
    def critical_stress(self):
        return critical_compression_stress_buckling_default(
            member_slenderness=self.slenderness,
            elastic_buckling_stress=self.elastic_buckling_stress,
            # member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.yield_stress,
        )

    @property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.critical_stress, sectional_area=self.section_area
        )


@dataclass
class FlexuralBucklingAdaptor(CriteriaAdaptor):
    section: Section
    beam: BeamGlobalData
    axis: Axis

    @property
    def beam_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def factor_k(self):
        table = {
            Axis.MAJOR: self.beam.buckling_param.factor_k_major_axis,
            Axis.MINOR: self.beam.buckling_param.factor_k_minor_axis,
        }
        return table[self.axis]

    @property
    def radius_of_gyration(self):
        table = {
            Axis.MAJOR: self.section.area_properties.major_axis.radius_of_gyration,
            Axis.MINOR: self.section.area_properties.minor_axis.radius_of_gyration,
        }
        return table[self.axis]

    @property
    def length(self):
        table = {
            Axis.MAJOR: self.beam.buckling_param.length_major_axis,
            Axis.MINOR: self.beam.buckling_param.length_minor_axis,
        }
        return table[self.axis]

    @property
    def beam_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k,
            radius_of_gyration=self.radius_of_gyration,
            unbraced_length=self.length,
        )

    @property
    def elastic_buckling_stress(self):
        return elastic_flexural_buckling_stress(
            modulus_linear=self.section.material.modulus_linear,
            member_slenderness_ratio=self.beam_slenderness,
        )

    @property
    def criteria(self) -> BucklingStrength:
        return BucklingStrength(
            elastic_buckling_stress=self.elastic_buckling_stress,
            slenderness=self.beam_slenderness,
            section_area=self.section.area_properties.area,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def critical_stress(self):
        return self.criteria.critical_stress


# def create_compression_flexural_buckling_criteria(
#     beam: BeamGlobalData, section: Section, axis: Literal["major", "minor"]
# ):
#     partial_creator = partial(
#         CompressionFlexuralBucklingCompact,
#         yield_stress=section.material.yield_stress,
#         modulus_linear=section.material.modulus_linear,
#         section_area=section.area_properties.area,
#         member_slenderness_limit=section.member_slenderness_limit,
#     )
#     table = {
#         "major": partial_creator(
#             radius_of_gyration=section.area_properties.major_axis.radius_of_gyration,
#             unbraced_length=beam_param.length_major_axis,
#             factor_k=beam_param.factor_k_major_axis,
#         ),
#         "minor": partial_creator(
#             radius_of_gyration=section.area_properties.minor_axis.radius_of_gyration,
#             unbraced_length=beam_param.unbraced_length_minor_axis,
#             factor_k=beam_param.factor_k_minor_axis,
#         ),
#     }
#     return table[axis]
