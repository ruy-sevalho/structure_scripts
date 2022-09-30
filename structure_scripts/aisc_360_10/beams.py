from dataclasses import dataclass
from functools import cached_property

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import SafetyFactor, AllowableStrengthDesign
from structure_scripts.aisc_360_10.sections import SectionProfile


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

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis
        if not self.unbraced_length_torsion:
            self.unbraced_length_torsion = self.unbraced_length_major_axis


@dataclass
class BeamAnalysis:
    beam_parameters: BeamParameters
    section: SectionProfile

    @cached_property
    def compression(self):
        return self.section.compression(beam_param=self.beam_parameters)