from functools import cached_property
from typing import Protocol, TYPE_CHECKING, Union, Optional
from dataclasses import dataclass
import pandas as pd

from quantities import Quantity, UnitQuantity, m, N

from structure_scripts.aisc_360_10.channel import Channel
from structure_scripts.aisc_360_10.criteria import (
    SafetyFactor, AllowableStrengthDesign, LoadAndResistanceFactorDesign, Criteria
)
from structure_scripts.aisc_360_10.i_profile import DoublySymmetricI
from structure_scripts.aisc_360_10.elements_latex import (
    BeamCompressionEffectiveLengthLatex, BeamFlexureDoublySymmetricLatex,
    BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex
)
from structure_scripts.aisc_360_10.helpers import (
    _critical_compression_stress_buckling_default,
    _elastic_flexural_buckling_stress,
    _flexural_flange_local_buckling_non_compact,
    _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric,
    _flexural_lateral_torsional_buckling_strength,
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b,
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c,
    _flexural_major_axis_yield_strength,
    _flexural_minor_axis_yield_strength, _flexural_and_axial_compression_h1_1_criteria,
    _lateral_torsional_buckling_modification_factor_default, _minimum_allowed_strength,
    _nominal_compressive_strength, _member_slenderness_limit,
    _web_shear_coefficient_limit, _nominal_shear_strength, _web_shear_coefficient_iii,
    ConstructionType
)
from structure_scripts.aisc_360_10.slenderness import Slenderness
from structure_scripts.aisc_360_10.sections import SectionProfile, SectionProfileWithWebAndFlange
from structure_scripts.shared.helpers import ratio_simplify, member_slenderness_ratio
from structure_scripts.shared.report_config import config_dict
from structure_scripts.shared.data import extract_input_dataframe

if TYPE_CHECKING:
    from structure_scripts.aisc_360_10.i_profile import DoublySymmetricI

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")


class BeamModelType(Protocol):
    profile: SectionProfile
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity
    unbraced_length_torsion: Quantity
    factor_k_minor_axis: float
    factor_k_major_axis: float
    factor_k_torsion: float
    lateral_torsional_buckling_modification_factor: float
    safety_factor: SafetyFactor


@dataclass
class ShearStrength(Criteria):
    """ Computes shear strength criteria in accordance to
    G2. MEMBERS WITH UNSTIFFENED OR STIFFENED WEBS
    1. Shear Strength
    """
    yield_stress: Quantity
    modulus_linear: Quantity
    web_slenderness_ratio: float
    web_area: Quantity
    web_plate_shear_buckling_coefficient: float
    rolled_i_shaped: bool = False
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    name = ""

    def __post_init__(self):
        # This code sure smells
        if self.rolled_i_shaped:
            if self.web_slenderness_ratio <= self.web_shear_coefficient_limit_0:
                if type(SafetyFactor) == AllowableStrengthDesign:
                    self.safety_factor.value = 1.5
                elif type(SafetyFactor) == LoadAndResistanceFactorDesign:
                    self.safety_factor.value = 1.0

    # @cached_property
    # def web_slenderness_ratio(self):
    #     return ratio_simplify(self.height, self.thickness)

    @cached_property
    def web_shear_coefficient_limit_0(self):
        return _web_shear_coefficient_limit(
            factor=2.24,
            web_shear_buckling_coefficient=1.,
            modulus_linear=self.modulus_linear,
            yield_stress=self.yield_stress
        )

    @cached_property
    def web_shear_coefficient_limit_i(self):
        return _web_shear_coefficient_limit(
            factor=1.1,
            web_shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
            modulus_linear=self.modulus_linear,
            yield_stress=self.yield_stress
        )

    @cached_property
    def web_shear_coefficient_limit_ii(self):
        return _web_shear_coefficient_limit(
            factor=1.37,
            web_shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
            modulus_linear=self.modulus_linear,
            yield_stress=self.yield_stress
        )

    @cached_property
    def web_shear_coefficient_iii(self):
        return _web_shear_coefficient_iii(
            shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
            modulus_linear=self.modulus_linear,
            yield_stress=self.yield_stress,
            web_slenderness=self.web_slenderness_ratio
        )

    @cached_property
    def web_shear_coefficient(self):
        if self.web_slenderness_ratio <= self.web_shear_coefficient_limit_0:
            return 1.0
        if self.web_slenderness_ratio < self.web_shear_coefficient_limit_i:
            return 1.0
        elif self.web_slenderness_ratio < self.web_shear_coefficient_limit_ii:
            return self.web_shear_coefficient_limit_i / self.web_slenderness_ratio
        else:
            return self.web_shear_coefficient_iii

    @cached_property
    def nominal_strength(self):
        return _nominal_shear_strength(
            yield_stress=self.yield_stress,
            web_area=self.web_area,
            web_shear_coefficient=self.web_shear_coefficient,
        )


@dataclass
class ShearMajorAxisAdaptor:
    profile: SectionProfileWithWebAndFlange
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def web_plate_shear_buckling_coefficient(self):
        # TODO implement different values for tee shape and stiffened sections once implemented
        return 5

    @cached_property
    def rolled(self):
        return self.profile.construction == ConstructionType.ROLLED and type(self.profile) in [DoublySymmetricI,]

    @property
    def criteria(self):
        return ShearStrength(
            yield_stress=self.profile.material.yield_stress,
            modulus_linear=self.profile.material.modulus_linear,
            web_slenderness_ratio=self.profile.slenderness.web.ratio,
            web_area=self.profile.slenderness.web.area_for_shear,
            web_plate_shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
            rolled_i_shaped=self.rolled_i_shape,
            safety_factor=self.safety_factor
        )


@dataclass
class ShearMinorAxisAdaptor:
    profile: SectionProfileWithWebAndFlange
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @property
    def criteria(self):
        return ShearStrength(
            yield_stress=self.profile.material.yield_stress,
            modulus_linear=self.profile.material.modulus_linear,
            web_slenderness_ratio=self.profile.slenderness.flange.ratio,
            web_area=self.profile.slenderness.flange.area_for_shear,
            web_plate_shear_buckling_coefficient=1.2,
            rolled_i_shaped=False,
            safety_factor=self.safety_factor
        )


def shear_major_axis(beam: BeamModelType) -> Criteria:
    return ShearMajorAxisAdaptor(profile=beam.profile, safety_factor=beam.safety_factor).criteria


def shear_minor_axis(beam: BeamModelType) -> Criteria:
    return ShearMinorAxisAdaptor(profile=beam.profile, safety_factor=beam.safety_factor).criteria


@dataclass
class ShearMajorAxis:
    beam: BeamModelType

    @cached_property
    def profile(self) -> SectionProfileWithWebAndFlange:
        return self.beam.profile

    @cached_property
    def criteria(self):
        return ShearMajorAxisAdaptor(profile=self.beam.profile, safety_factor=self.beam.safety_factor)


@dataclass
class ShearMinorAxis:
    beam: BeamModelType

    @cached_property
    def criteria(self):
        return ShearMinorAxisAdaptor(profile=self.beam.profile, safety_factor=self.beam.safety_factor)


@dataclass
class BeamShearWeb:
    profile: SectionProfileWithWebAndFlange
    required_strength_major_axis: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    def __post_init__(self):
        # This code sure smells
        if type(self.profile) == DoublySymmetricI:
            profile: DoublySymmetricI = self.profile
            if profile.construction == ConstructionType.ROLLED:
                if self.profile.slenderness.web.ratio <= self.profile.web_shear_coefficient_limit_0:
                    if type(SafetyFactor) == AllowableStrengthDesign:
                        self.safety_factor.value = 1.5
                    elif type(SafetyFactor) == LoadAndResistanceFactorDesign:
                        self.safety_factor.value = 1.0

    @cached_property
    def nominal_strength(self):
        return _nominal_shear_strength(
            yield_stress=self.profile.material.yield_stress,
            web_area=self.profile.area_properties.web_area,
            web_shear_coefficient=self.profile.web_shear_coefficient,
        )

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength shear": [self.design_strength.rescale(kN)]
            }
        )

    @cached_property
    def criteria_df(self):
        return pd.DataFrame(
            {
                "shear_stress_criteria": [ratio_simplify(self.required_strength_major_axis, self.design_strength)]
            }
        )


@dataclass
class CompressionFlexuralBuckling(Criteria):
    unbraced_length: Quantity
    factor_k: float
    radius_of_gyration: Quantity
    section_area: Quantity
    modulus_linear: Quantity
    yield_stress: Quantity
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
    def member_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.modulus_linear,
            yield_stress=self.yield_stress
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


@dataclass
class BeamCompressionFlexuralBuckling:
    profile: SectionProfile
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    required_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis
        # if not self.unbraced_length_torsion:
        #     self.unbraced_length_torsion = self.unbraced_length_major_axis

    @cached_property
    def minor_axis_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k_minor_axis,
            radius_of_gyration=self.profile.area_properties.minor_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length_minor_axis
        )

    @cached_property
    def major_axis_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k_major_axis,
            radius_of_gyration=self.profile.area_properties.major_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length_major_axis
        )

    @cached_property
    def elastic_flexural_buckling_stress_minor_axis(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.minor_axis_slenderness
        )

    @cached_property
    def elastic_flexural_buckling_stress_major_axis(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.major_axis_slenderness
        )

    @cached_property
    def member_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def flexural_buckling_critical_stress_minor_axis(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.minor_axis_slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress_minor_axis,
            member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def flexural_buckling_critical_stress_major_axis(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.major_axis_slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress_major_axis,
            member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def critical_stress_flexural_buckling(self) -> Quantity:
        return min(self.flexural_buckling_critical_stress_minor_axis, self.flexural_buckling_critical_stress_major_axis)

    @cached_property
    def nominal_strength(self) -> Quantity:
        return min(self.strength_minor_axis_flexural_buckling, self.strength_major_axis_flexural_buckling)

    @cached_property
    def strength_minor_axis_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress_minor_axis,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_major_axis_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress_major_axis,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def design_strength_minor_axis(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength flexural buckling minor axis": [self.design_strength.rescale(kN)],
            }
        )

    @cached_property
    def latex(self):
        return BeamCompressionEffectiveLengthLatex(self)


@dataclass
class BeamCompressionTorsionalBuckling:
    profile: SectionProfile
    unbraced_length: Quantity
    factor_k: float = 1.0
    required_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def torsional_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k,
            radius_of_gyration=self.profile.area_properties.major_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length
        )

    @cached_property
    def torsional_critical_stress(self):
        return self.profile.torsional_buckling_critical_stress_effective_length(self)

    @cached_property
    def member_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            self.torsional_critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength torsional buckling": [self.design_strength.rescale(kN)]
            }
        )


class BeamFlexure(Protocol):
    strength_yielding: Quantity
    strength_lateral_torsional_buckling: Quantity | None
    strength_compression_local_buckling: Quantity | None


@dataclass
class LateralTorsionalBucklingModificationFactorDefault:
    moment_max: Quantity
    moment_quarter: Quantity
    moment_center: Quantity
    moment_three_quarter: Quantity

    @cached_property
    def value(self):
        return _lateral_torsional_buckling_modification_factor_default(
            self.moment_max,
            self.moment_quarter,
            self.moment_center,
            self.moment_three_quarter
        )


def lateral_torsional_buckling_modification_factor_default(
        moment_max: Quantity,
        moment_quarter: Quantity,
        moment_center: Quantity,
        moment_three_quarter: Quantity
):
    return _lateral_torsional_buckling_modification_factor_default(
        moment_max,
        moment_quarter,
        moment_center,
        moment_three_quarter
    )


@dataclass
class BeamFlexureDoublySymmetric:
    profile: SectionProfile
    unbraced_length_major_axis: Quantity
    lateral_torsional_buckling_modification_factor: float = 1.
    required_major_axis_flexural_strength: Quantity | None = None
    required_minor_axis_flexural_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def plastic_moment_major_axis(self) -> Quantity:
        return self.strength_major_axis_yield

    @cached_property
    def strength_major_axis_yield(self) -> Quantity:
        return _flexural_major_axis_yield_strength(
            self.profile.material.yield_stress,
            self.profile.area_properties.major_axis_plastic_section_modulus
        )

    # Doubly symmetric I I
    @cached_property
    def strength_lateral_torsion_compact_case_b(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.unbraced_length_major_axis,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
            limiting_length_yield=self.profile.limit_length_yield,
            mod_factor=self.lateral_torsional_buckling_modification_factor,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    # Doubly symmetric I
    @cached_property
    def critical_stress_lateral_torsional_buckling(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=self.lateral_torsional_buckling_modification_factor,
            length_between_braces=self.unbraced_length_major_axis,
            modulus=self.profile.material.modulus_linear,
            coefficient_c=self.profile.coefficient_c,
            distance_between_flange_centroids=self.profile.dimensions.distance_between_centroids,
            effective_radius_of_gyration=self.profile.effective_radius_of_gyration,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.profile.area_properties.torsional_constant
        )

    @cached_property
    def strength_lateral_torsion_compact_case_c(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            critical_stress=self.critical_stress_lateral_torsional_buckling,
        )

    # Doubly symmetric I
    @cached_property
    def strength_lateral_torsion(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength(
            case_b=self.strength_lateral_torsion_compact_case_b,
            case_c=self.strength_lateral_torsion_compact_case_c,
            length_between_braces=self.unbraced_length_major_axis,
            limiting_length_yield=self.profile.limit_length_yield,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
        )

    @cached_property
    def strength_major_axis_flange_local_buckling_slender(self):
        raise NotImplementedError

    @cached_property
    def strength_major_axis_flange_local_buckling_non_compact(self) -> Quantity:
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange.flexural_major_axis.compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange.flexural_major_axis.slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange.ratio,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def strength_minor_axis_flange_local_buckling_non_compact(self) -> Quantity:
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange.flexural_minor_axis.compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange.flexural_minor_axis.slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange.ratio,
            plastic_moment=self.plastic_moment_minor_axis,
            section_modulus=self.profile.area_properties.minor_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    def strength_minor_axis_flange_local_buckling_slender(self):
        raise NotImplementedError

    @cached_property
    def strength_minor_axis_yield(self) -> Quantity:
        return _flexural_minor_axis_yield_strength(
            yield_stress=self.profile.material.yield_stress,
            elastic_section_modulus=self.profile.area_properties.minor_axis_elastic_section_modulus,
            plastic_section_modulus=self.profile.area_properties.minor_axis_plastic_section_modulus
        )

    @cached_property
    def plastic_moment_minor_axis(self) -> Quantity:
        return self.strength_minor_axis_yield

    @cached_property
    def strength_major_axis_flange_local_buckling(self) -> Quantity:
        # TODO Implement slender flange local buckling strength
        table = {
            Slenderness.COMPACT: None,
            Slenderness.NON_COMPACT: self.strength_major_axis_flange_local_buckling_non_compact,
            # Slenderness.SLENDER: self.strength_major_axis_flange_local_buckling_slender,
        }
        return table[self.profile.slenderness.flange.flexural_major_axis.value]

    @cached_property
    def strength_minor_axis_flange_local_buckling(self) -> Quantity:
        table = {
            Slenderness.COMPACT: None,
            Slenderness.NON_COMPACT: self.strength_minor_axis_flange_local_buckling_non_compact,
            Slenderness.SLENDER: self.strength_minor_axis_flange_local_buckling_slender,
        }
        return table[self.profile.slenderness.flange.flexural_major_axis.value]

    @cached_property
    def nominal_strength_major_axis(self) -> Quantity:
        yield_ = self.strength_major_axis_yield
        lateral_torsional_buckling = self.strength_lateral_torsion
        flange_local_buckling = self.strength_major_axis_flange_local_buckling
        strengths = (yield_, lateral_torsional_buckling, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    @cached_property
    def nominal_strength_minor_axis(self) -> Quantity:
        yield_ = self.strength_minor_axis_yield
        flange_local_buckling = self.strength_minor_axis_flange_local_buckling
        strengths = (yield_, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    @cached_property
    def design_strength_major_axis(self) -> Quantity:
        return self.safety_factor.allowable_value(self.nominal_strength_major_axis)

    @cached_property
    def design_strength_minor_axis(self) -> Quantity:
        return self.safety_factor.allowable_value(self.nominal_strength_minor_axis)

    @cached_property
    def strength_resume(self) -> pd.DataFrame:
        strength_local_buckling = self.strength_major_axis_flange_local_buckling
        df = {
            "strength yield": [self.safety_factor.allowable_value(self.strength_major_axis_yield).rescale(kN * m)],
        }
        if self.strength_lateral_torsion:
            df.update(
                {
                    "strength lateral torsion": [
                        self.safety_factor.allowable_value(
                            self.strength_lateral_torsion
                        ).rescale(kN * m)
                    ]
                }
            )
        if self.strength_major_axis_flange_local_buckling:
            df.update(
                {
                    "strength local buckling": [
                        self.safety_factor.allowable_value(strength_local_buckling).rescale(kN * m)
                    ]
                }
            )
        return pd.DataFrame(df)

    @cached_property
    def latex(self):
        return BeamFlexureDoublySymmetricLatex(self)


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLength:
    profile: SectionProfile
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    lateral_torsional_buckling_modification_factor: float = 1.0
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()
    required_axial_strength: Quantity = 0 * N
    required_major_axis_flexural_strength: Quantity = 0 * N * m
    required_minor_axis_flexural_strength: Quantity = 0 * N * m

    def table(self, filter_names: list[str] = None):
        return extract_input_dataframe(obj=self, extraction_type=self, filter_names=filter_names)

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis

    @cached_property
    def data_table_df(self):
        return self.table(
            filter_names=[
                "profile",
                "safety_factor",
                "required_axial_strength",
                "required_major_axis_flexural_strength",
                "required_minor_axis_flexural_strength"

            ]
        )

    @cached_property
    def compression(self):
        return BeamCompressionFlexuralBuckling(
            profile=self.profile,
            unbraced_length_major_axis=self.unbraced_length_major_axis,
            unbraced_length_minor_axis=self.unbraced_length_minor_axis,
            factor_k_major_axis=self.factor_k_major_axis,
            factor_k_minor_axis=self.factor_k_minor_axis,
            factor_k_torsion=self.factor_k_torsion,
            required_strength=self.required_axial_strength
        )

    @cached_property
    def flexure(self):
        return BeamFlexureDoublySymmetric(
            profile=self.profile,
            unbraced_length_major_axis=self.unbraced_length_major_axis,
            required_major_axis_flexural_strength=self.required_major_axis_flexural_strength,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexural_strength
        )

    @cached_property
    def compression_flexure_combined_criteria_h1_1(self) -> float:
        return _flexural_and_axial_compression_h1_1_criteria(
            available_axial_strength=self.compression.design_strength,
            required_axial_strength=self.required_axial_strength,
            available_major_axis_flexural_strength=self.flexure.design_strength_major_axis,
            required_major_axis_flexural_strength=self.required_major_axis_flexural_strength,
            available_minor_axis_flexural_strength=self.flexure.design_strength_minor_axis,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexural_strength,
        )

    @cached_property
    def resume(self):
        return pd.concat((self.compression.strength_resume, self.flexure.strength_resume), axis=1)

    @cached_property
    def latex(self):
        return BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex(self)

    @cached_property
    def required_strengths_df(self):
        return pd.DataFrame(
            {
                "required_axial_strength": [self.required_axial_strength.magnitude],
                "required_major_axis_flexure_strength": [self.required_major_axis_flexural_strength.magnitude],
                "required_minor_axis_flexure_strength": [self.required_minor_axis_flexural_strength.magnitude],
            }
        )

    @cached_property
    def criteria_df(self):
        return pd.DataFrame({"h1_criteria": [abs(self.compression_flexure_combined_criteria_h1_1)]})

    @cached_property
    def results_h1_df(self):
        required_df = self.required_strengths_df
        return pd.concat(
            (required_df, self.criteria_df,),
            axis=1,
        )


@dataclass
class BeamParameters:
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    unbraced_length_torsion: Quantity | None = None
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    lateral_torsional_buckling_modification_factor: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()


@dataclass
class BeamModel:
    profile: SectionProfile
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    unbraced_length_torsion: Quantity | None = None
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    lateral_torsional_buckling_modification_factor: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis
        if not self.unbraced_length_torsion:
            self.unbraced_length_torsion = self.unbraced_length_major_axis

    table_shear_major_axis = {
        DoublySymmetricI: (shear_major_axis,),
        Channel: (shear_major_axis,)
    }

    table_shear_minor_axis = {
        DoublySymmetricI: (shear_minor_axis,),
        Channel: (shear_minor_axis,)
    }

    @cached_property
    def shear_major_axis_criteria(self):
        return tuple(criteria(self) for criteria in self.table_shear_major_axis[type(self.profile)])

    @cached_property
    def shear_major_axis_design_strength(self):
        return

    def result(
            self,
            required_axial_strength: Quantity = 0 * N,
            required_major_axis_flexural_strength: Quantity = 0 * N * m,
            required_minor_axis_flexural_strength: Quantity = 0 * N * m,
            required_major_axis_shear_strength: Quantity = 0 * N,
            required_minor_axis_shear_strength: Quantity = 0 * N,
            required_torsional_strength: Quantity = 0 * N * m,
            safety_factor: SafetyFactor = AllowableStrengthDesign(),
    ):
        return BeamResult(
            model=self,
            required_axial_strength=required_axial_strength,
            required_major_axis_flexural_strength=required_major_axis_flexural_strength,
            required_minor_axis_flexural_strength=required_minor_axis_flexural_strength,
            required_major_axis_shear_strength=required_major_axis_shear_strength,
            required_minor_axis_shear_strength=required_minor_axis_shear_strength,
            required_torsional_strength=required_torsional_strength,
            safety_factor=safety_factor
        )


@dataclass
class BeamResult:
    model: BeamModel
    required_axial_strength: Quantity = 0 * N
    required_major_axis_flexural_strength: Quantity = 0 * N * m
    required_minor_axis_flexural_strength: Quantity = 0 * N * m
    required_major_axis_shear_strength: Quantity = 0 * N
    required_minor_axis_shear_strength: Quantity = 0 * N
    required_torsional_strength: Quantity = 0 * N * m
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def compression_flexure_analysis(self):
        return BeamCompressionFlexureDoublySymmetricEffectiveLength(
            profile=self.model.profile,
            unbraced_length_minor_axis=self.model.unbraced_length_minor_axis,
            unbraced_length_major_axis=self.model.unbraced_length_major_axis,
            lateral_torsional_buckling_modification_factor=self.lateral_torsional_buckling_modification_factor,
            factor_k_major_axis=self.model.factor_k_major_axis,
            factor_k_minor_axis=self.model.factor_k_minor_axis,
            safety_factor=self.safety_factor,
            required_axial_strength=self.required_axial_strength,
            required_major_axis_flexural_strength=self.required_major_axis_flexural_strength,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexural_strength
        )

    @cached_property
    def compression_analysis(self):
        return self.compression_flexure_analysis.compression

    @cached_property
    def flexure_analysis(self):
        return self.compression_flexure_analysis.flexure

    @cached_property
    def shear_analysis(self):
        return BeamShearWeb(
            profile=self.model.profile,
            required_strength=self.required_major_axis_shear_strength,
            safety_factor=self.safety_factor
        )

    @cached_property
    def critical_strengths(self):
        df = pd.concat(
            (
                self.compression_flexure_analysis.compression.strength_resume,
                self.compression_flexure_analysis.flexure.strength_resume,
                self.shear_analysis.strength_resume,
            ),
            axis=1
        )
        return df

    @cached_property
    def required_strengths_df(self):
        return pd.DataFrame(
            {
                "axial load": [self.required_axial_strength.rescale(config_dict.required_axial_strength.print_units)],
                "major axis load": [self.required_major_axis_flexural_strength.rescale(
                    config_dict.required_major_axis_flexural_strength.print_units)],
                "minor axis load": [self.required_minor_axis_flexural_strength.rescale(
                    config_dict.required_major_axis_flexural_strength.print_units)],
                "shear load": [
                    self.required_major_axis_shear_strength.rescale(config_dict.required_axial_strength.print_units)],
                "torsion load": [self.required_torsional_strength.rescale(
                    config_dict.required_major_axis_flexural_strength.print_units)]
            }
        )

    @cached_property
    def results(self):
        return pd.concat(
            (
                self.required_strengths_df,
                self.compression_flexure_analysis.criteria_df,
                self.shear_analysis.criteria_df
            ),
            axis=1
        )
