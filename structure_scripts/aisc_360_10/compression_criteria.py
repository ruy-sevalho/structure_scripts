from dataclasses import dataclass
from functools import cached_property, partial
from typing import Literal

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import Criteria, SafetyFactor, AllowableStrengthDesign
from structure_scripts.aisc_360_10.beams import BeamParameters
from structure_scripts.aisc_360_10.helpers import _elastic_flexural_buckling_stress, _member_slenderness_limit, \
    _critical_compression_stress_buckling_default, _nominal_compressive_strength
from structure_scripts.aisc_360_10.sections import SectionProfile
from structure_scripts.shared.helpers import member_slenderness_ratio

FLEXURAL_BUCKLING = "flexural_buckling"
TORSIONAL_BUCKLING = "torsional_buckling"


@dataclass
class CompressionFlexuralBucklingCompact(Criteria):
    unbraced_length: Quantity
    factor_k: float
    radius_of_gyration: Quantity
    section_area: Quantity
    modulus_linear: Quantity
    yield_stress: Quantity
    member_slenderness_limit: float
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k,
            radius_of_gyration=self.radius_of_gyration,
            unbraced_length=self.unbraced_length
        )

    @cached_property
    def elastic_flexural_buckling_stress(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.modulus_linear,
            member_slenderness_ratio=self.slenderness
        )

    @cached_property
    def flexural_buckling_critical_stress(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress,
            member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.yield_stress
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress,
            sectional_area=self.section_area
        )


def create_compression_flexural_buckling_criteria(
        beam_param: BeamParameters, section: SectionProfile, axis: Literal["major", "minor"]
):
    partial_creator = partial(
        CompressionFlexuralBucklingCompact,
        yield_stress=section.material.yield_stress,
        modulus_linear=section.material.modulus_linear,
        section_area=section.area_properties.area,
        member_slenderness_limit=section.member_slenderness_limit
    )
    table = {
        'major': partial_creator(
            radius_of_gyration=section.area_properties.major_axis_radius_of_gyration,
            unbraced_length=beam_param.unbraced_length_major_axis,
            factor_k=beam_param.factor_k_major_axis,
        ),
        'minor': partial_creator(
            radius_of_gyration=section.area_properties.minor_axis_radius_of_gyration,
            unbraced_length=beam_param.unbraced_length_minor_axis,
            factor_k=beam_param.factor_k_minor_axis,
        )
    }
    return table[axis]
