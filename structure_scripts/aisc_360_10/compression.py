import abc
from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    # SafetyFactor,
    # AllowableStrengthDesign,
    # CriteriaAdaptor,
    NOMINAL_STRENGTH,
)
from structure_scripts.aisc_360_10.beams import (
    Beam,
)
from structure_scripts.aisc_360_10.helpers import (
    elastic_flexural_buckling_stress,
    critical_compression_stress_buckling_default,
    _nominal_compressive_strength,
    elastic_torsional_buckling_stress_doubly_symmetric_member,
)

from structure_scripts.aisc_360_10.sections import Section
from structure_scripts.helpers import member_slenderness_ratio, Axis

if TYPE_CHECKING:
    from structure_scripts.aisc_360_10.i_profile import DoublySymmetricI

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


class BucklingStrengthGeneralCalculation(Strength, Protocol):
    critical_stress: Quantity


class BucklingStrengthEulerCalculation(
    BucklingStrengthGeneralCalculation, Protocol
):
    elastic_buckling_stress: Quantity


@dataclass
class BucklingStrength:
    elastic_buckling_stress: Quantity
    section_area: Quantity
    yield_stress: Quantity

    @property
    def critical_stress(self):
        return critical_compression_stress_buckling_default(
            elastic_buckling_stress=self.elastic_buckling_stress,
            yield_stress=self.yield_stress,
        )

    @property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.critical_stress,
            sectional_area=self.section_area,
        )


class BucklingMixin(abc.ABC):
    section: Section

    @property
    def buckling_strength_model(self) -> BucklingStrength:
        return BucklingStrength(
            elastic_buckling_stress=self.elastic_buckling_stress,
            section_area=self.section.area_properties.area,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def nominal_strength(self):
        return self.buckling_strength_model.nominal_strength

    @property
    def critical_stress(self):
        return self.buckling_strength_model.critical_stress

    @property
    def detailed_results(self):
        return {
            ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
            BUCKLING_CRITICAL_STRESS: self.critical_stress,
            NOMINAL_STRENGTH: self.nominal_strength,
        }


@dataclass
class FlexuralBuckling(BucklingMixin):
    section: Section
    beam: Beam
    axis: Axis

    @property
    def valid(self) -> bool:
        return True

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

    # @property
    # def buckling_strength_model(self) -> BucklingStrength:
    #     return BucklingStrength(
    #         elastic_buckling_stress=self.elastic_buckling_stress,
    #         section_area=self.section.area_properties.area,
    #         yield_stress=self.section.material.yield_stress,
    #     )

    # @property
    # def nominal_strength(self):
    #     return self.buckling_strength_model.nominal_strength

    # @property
    # def critical_stress(self):
    #     return self.buckling_strength_model.critical_stress

    # @property
    # def detailed_results(self):
    #     return {
    #         ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
    #         BUCKLING_CRITICAL_STRESS: self.critical_stress,
    #         NOMINAL_STRENGTH: self.nominal_strength,
    #     }


@dataclass
class TorsionalBucklingDoublySymmetricI(BucklingMixin):
    section: "DoublySymmetricI"
    beam: Beam

    @property
    def valid(self) -> bool:
        return True

    @property
    def elastic_buckling_stress(self):
        return elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.section.material.modulus_linear,
            factor_k=self.beam.buckling_param.factor_k_torsion,
            length=self.beam.buckling_param.length_torsion,
            major_axis_inertia=self.section.area_properties.major_axis.inertia,
            minor_axis_inertia=self.section.area_properties.minor_axis.inertia,
            torsional_constant=self.section.area_properties.torsion.inertia,
            modulus_shear=self.section.material.modulus_shear,
        )

    # @property
    # def buckling_strength(self) -> BucklingStrength:
    #     return BucklingStrength(
    #         elastic_buckling_stress=self.elastic_buckling_stress,
    #         section_area=self.section.area_properties.area,
    #         yield_stress=self.section.material.yield_stress,
    #     )

    # @property
    # def nominal_strength(self):
    #     return self.buckling_strength.nominal_strength

    # @property
    # def critical_stress(self):
    #     return self.buckling_strength.critical_stress

    # @property
    # def detailed_results(self):
    #     return {
    #         ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
    #         BUCKLING_CRITICAL_STRESS: self.critical_stress,
    #         FLEXURAL_BUCKLING_MAJOR_AXIS_STRENGTH: self.nominal_strength,
    #     }


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
