from dataclasses import dataclass

from quantities import Quantity

from structure_scripts.aisc.compression import FlexuralBucklingStrength
from structure_scripts.aisc.criteria import DesignStrength, StrengthType
from structure_scripts.aisc.sections import (
    AISC_360_10_Rule_Check,
    AISC_Section,
    ConstructionType,
)
from structure_scripts.helpers import Axis
from structure_scripts.materials import IsotropicMaterial


@dataclass(frozen=True)
class AngleAISC36010:
    # dimensions: "DoublySymmetricIDimensions"
    section: AISC_Section
    material: IsotropicMaterial
    construction: ConstructionType = ConstructionType.ROLLED
    # coefficient_c: float = 1.0

    def compression(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
    ) -> DesignStrength:
        length_minor_axis = length_minor_axis or length_major_axis
        length_torsion = length_torsion or length_major_axis
        flexural_buckling_major_axis = FlexuralBucklingStrength(
            profile=self,
            length=length_major_axis,
            factor_k=factor_k_major_axis,
            axis=Axis.MAJOR,
        )
        flexural_buckling_minor_axis = FlexuralBucklingStrength(
            profile=self,
            length=length_minor_axis,
            factor_k=factor_k_minor_axis,
            axis=Axis.W,
        )
        # torsional_buckling_strength = TorsionalBucklingDoublySymmetricI(
        #     profile=self, length=length_torsion, factor_k=factor_k_torsion
        # )
        return DesignStrength(
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis,
            }
        )
