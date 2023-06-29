from dataclasses import dataclass
from functools import cached_property

from quantities import Quantity

from structure_scripts.aisc.compression import FlexuralBucklingStrength
from structure_scripts.aisc.criteria import DesignStrength, StrengthType, Strength
from structure_scripts.aisc.flexure import MinorAxisFlexurePlasticYielding, MajorAxisFlexurePlasticYielding
from structure_scripts.aisc.i_section import TorsionalBucklingDoublySymmetricI
from structure_scripts.aisc.sections import AISC_360_10_Rule_Check, AISC_Section, ConstructionType
from structure_scripts.aisc.shear import StandardShearCriteriaAdaptor
from structure_scripts.helpers import Axis
from structure_scripts.materials import IsotropicMaterial


@dataclass(frozen=True)
class Pipe(AISC_360_10_Rule_Check):

    section: AISC_Section
    material: IsotropicMaterial
    construction: ConstructionType = ConstructionType.ROLLED

    # using minor axis for I shapes which corresponds to formulation for round pipes
    @cached_property
    def flex_yield_major_axis(self) -> Strength:
        return MinorAxisFlexurePlasticYielding(self)

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
        # length_torsion = length_torsion or length_major_axis
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
            axis=Axis.MINOR,
        )
        return DesignStrength(
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis,
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis,
            }
        )

    def flexure_major_axis(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
    ) -> DesignStrength:
        nominal_strengths = {
            StrengthType.YIELD: self.flex_yield_major_axis,
        }
        # if (
        #     self.slenderness.flange_flexure_major_axis
        #     == Slenderness.NON_COMPACT
        # ):
        #     nominal_strengths.update(
        #         {
        #             StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING: self.flex_major_axis_non_compact_flange_local_buckling
        #         }
        #     )
        return DesignStrength(nominal_strengths=nominal_strengths)

    def flexure_minor_axis(
        self,
    ) -> DesignStrength:
        nominal_strengths = {
            StrengthType.YIELD: self.flex_yield_major_axis
        }
        # if (
        #     self.slenderness.flange_flexure_minor_axis
        #     == Slenderness.NON_COMPACT
        # ):
        #     nominal_strengths.update(
        #         {
        #             StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING: self.flex_minor_axis_non_compact_flange_local_buckling
        #         }
        #     )

        return DesignStrength(nominal_strengths=nominal_strengths)

    @cached_property
    def shear_major_axis_area(self):
        return self.section.A

    @cached_property
    def shear_minor_axis_area(self):
        return self.section.A

    @cached_property
    def _shear_major_axis(self) -> DesignStrength:
        return DesignStrength()
        # return DesignStrength(
        #     nominal_strengths={
        #         StrengthType.YIELD: StandardShearCriteriaAdaptor(
        #             section=self,
        #             axis=Axis.MAJOR,
        #         ),
        #     }
        # )

    def shear_major_axis(self) -> DesignStrength:
        return self._shear_major_axis

    @cached_property
    def _shear_minor_axis(self) -> DesignStrength:
        return DesignStrength()
        # return DesignStrength(
        #     nominal_strengths={
        #         StrengthType.YIELD: StandardShearCriteriaAdaptor(
        #             section=self,
        #             axis=Axis.MINOR,
        #         ),
        #     }
        # )

    def shear_minor_axis(self) -> DesignStrength:
        return self._shear_minor_axis
