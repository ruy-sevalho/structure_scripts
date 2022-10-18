from dataclasses import dataclass
from functools import cached_property
from typing import Protocol

from quantities import Quantity, N, m

from structure_scripts.aisc_360_10.criteria import SafetyFactor, AllowableStrengthDesign
from structure_scripts.aisc_360_10.helpers import _member_slenderness_limit
from structure_scripts.aisc_360_10.sections import Section
from structure_scripts.shared.helpers import member_slenderness_ratio


# class BeamParameters(Protocol):
#     unbraced_length_major_axis: Quantity
#     unbraced_length_minor_axis: Quantity
#     unbraced_length_torsion: Quantity
#     factor_k_minor_axis: float
#     factor_k_major_axis: float
#     factor_k_torsion: float
#     # lateral_torsional_buckling_modification_factor: float
#     # axial_force: Quantity | None
#     # major_axis_bending_moment: Quantity | None
#     # major_axis_shear_force: Quantity | None
#     # minor_axis_bending_moment: Quantity | None
#     # minor_axis_shear_force: Quantity | None
#     # torsion_moment: Quantity | None
#     safety_factor: SafetyFactor
#

# @dataclass
# class BeamParametersData(BeamParameters):
#     unbraced_length_major_axis: Quantity
#     unbraced_length_minor_axis: Quantity | None = None
#     unbraced_length_torsion: Quantity | None = None
#     factor_k_minor_axis: float = 1.0
#     factor_k_major_axis: float = 1.0
#     factor_k_torsion: float = 1.0
    # lateral_torsional_buckling_modification_factor: float = 1.0
    # axial_force: Quantity | None = None
    # major_axis_bending_moment: Quantity | None = None
    # major_axis_shear_force: Quantity | None = None
    # minor_axis_bending_moment: Quantity | None = None
    # minor_axis_shear_force: Quantity | None = None
    # torsion_moment: Quantity | None = None

    # def __post_init__(self):
    #     if not self.unbraced_length_minor_axis:
    #         self.unbraced_length_minor_axis = self.unbraced_length_major_axis
    #     if not self.unbraced_length_torsion:
    #         self.unbraced_length_torsion = self.unbraced_length_major_axis


class BeamLoading(Protocol):
    axial_force: Quantity | None = None
    major_axis_bending_moment: Quantity | None = None
    major_axis_shear_force: Quantity | None = None
    minor_axis_bending_moment: Quantity | None = None
    minor_axis_shear_force: Quantity | None = None
    torsion_moment: Quantity | None = None


@dataclass
class BeamLoadingData(BeamLoading):
    axial_force: Quantity | None = None
    major_axis_bending_moment: Quantity | None = None
    major_axis_shear_force: Quantity | None = None
    minor_axis_bending_moment: Quantity | None = None
    minor_axis_shear_force: Quantity | None = None
    torsion_moment: Quantity | None = None


class BeamSlenderness(Protocol):
    major_axis: float
    minor_axis: float
    torsion: float


@dataclass
class BucklingParam:
    length_major_axis: Quantity
    factor_k_major_axis: float = 1.0
    length_minor_axis: Quantity = None
    factor_k_minor_axis: float = 1.0
    length_torsion: Quantity = None
    factor_k_torsion: float = 1.0

    def __post_init__(self):
        self.length_minor_axis = self.length_minor_axis or self.length_major_axis
        self.length_torsion = self.length_torsion or self.length_major_axis


@dataclass
class BeamGlobalData:
    """buckling_param: BucklingParam
    loads: BeamLoading | None = None
    lateral_torsional_buckling_modification_factor: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()
    """
    buckling_param: BucklingParam
    loads: BeamLoading | None = None
    lateral_torsional_buckling_modification_factor: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()


@dataclass
class BeamAnalysis:
    section: Section
    beam: BeamGlobalData


    @cached_property
    def slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress
        )

    @cached_property
    def major_axis_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.beam.buckling_param.factor_k_major_axis,
            unbraced_length=self.beam.buckling_param.length_major_axis,
            radius_of_gyration=self.section.area_properties.major_axis.radius_of_gyration
        )

    @cached_property
    def minor_axis_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.beam.buckling_param.factor_k_minor_axis,
            unbraced_length=self.beam.buckling_param.length_minor_axis,
            radius_of_gyration=self.section.area_properties.minor_axis.radius_of_gyration
        )

    @cached_property
    def torsion_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.beam.buckling_param.factor_k_torsion,
            unbraced_length=self.beam.buckling_param.length_torsion,
            radius_of_gyration=self.section.area_properties.torsion.radius_of_gyration
        )

    @cached_property
    def compression(self):
        return self.section.compression(beam=self.beam)

    @cached_property
    def shear_major_axis(self):
        return self.section.shear_major_axis(beam=self.beam)
