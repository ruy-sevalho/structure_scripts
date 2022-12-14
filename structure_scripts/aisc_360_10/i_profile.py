from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

from quantities import Quantity

from structure_scripts.aisc_360_10.compression import (
    BucklingStrengthMixin,
    FlexuralBucklingStrength,
    ELASTIC_BUCKLING_STRESS,
)
from structure_scripts.aisc_360_10.criteria import (
    DesignType,
    StrengthType,
    DesignStrength, Strength,
)
from structure_scripts.aisc_360_10.flexure import (
    MajorAxisFlexurePlasticYielding,
    LateralTorsionalBuckling,
    MinorAxisFlexurePlasticYielding, NonCompactFlangeLocalBuckling, SlenderFlangeLocalBuckingMajorAxis,
)
from structure_scripts.aisc_360_10.helpers import (
    limit_ratio_default,
    kc_coefficient,
    limit_stress_built_up_sections,
    elastic_torsional_buckling_stress_doubly_symmetric_member,
)
from structure_scripts.aisc_360_10.sections import (
    AISC_360_10_Rule_Check,
)
from structure_scripts.section_slenderness import (
    axial_slenderness_per_element,
    flexural_slenderness_per_element,
    DoublySymmetricIAndChannelSlenderness,
    DoublySymmetricIAndChannelSlendernessCalcMemory,
    DoublySymmetricIAndChannelAxialCalcMemory,
    AxialSlendernessCalcMemory,
    FlexuralSlendernessCalcMemory,
    DoublySymmetricIAndChannelFlexureMajorAxisCalcMemory,
    DoublySymmetricIAndChannelFlexureMinorAxisCalcMemory, Slenderness,
)
from structure_scripts.helpers import (
    Axis,
)
from structure_scripts.materials import IsotropicMaterial
from structure_scripts.section import AISC_Section, Profile, SectionType

from structure_scripts.section_properties import (
    ConstructionType,
)

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class DoublySymmetricIWebSlenderness:
    profile: Profile

    @cached_property
    def ratio(self):
        return self.profile.section.h_tw

    @cached_property
    def axial_limit(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.49,
        )

    @cached_property
    def flexural_compact_non_compact_limit(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=3.76,
        )

    @cached_property
    def flexural_non_compact_slender_limit(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=5.7,
        )

    @cached_property
    def axial(self):
        return axial_slenderness_per_element(
            limit=self.axial_limit,
            slenderness=self.ratio,
        )

    @cached_property
    def flexural_major_axis(self):
        return flexural_slenderness_per_element(
            ratio=self.ratio,
            limit_slender=self.flexural_non_compact_slender_limit,
            limit_compact=self.flexural_compact_non_compact_limit,
        )


@dataclass(frozen=True)
class DoublySymmetricIFlangeSlenderness:
    profile: Profile

    @cached_property
    def ratio(self):
        table = {
            SectionType.C: self.profile.section.b_t
        }
        return table.get(self.profile.section.type, self.profile.section.bf_2tf)

    @cached_property
    def kc_coefficient(self):
        return kc_coefficient(h_tw=self.profile.section.h_tw)

    @cached_property
    def axial_limit_ratio_rolled(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.56,
        )

    @cached_property
    def axial_limit_ratio_built_up(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.64,
            kc_coefficient=self.kc_coefficient,
        )

    @cached_property
    def axial_limit(self):
        table = {
            ConstructionType.ROLLED: self.axial_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.axial_limit_ratio_built_up,
        }
        return table[self.profile.construction]

    @cached_property
    def flexural_compact_non_compact_limit(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.38,
        )

    @cached_property
    def flexural_slender_limit_ratio_rolled(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.0,
        )

    @cached_property
    def flexural_slender_limit_ratio_built_up(self):
        stress = limit_stress_built_up_sections(
            yield_stress=self.profile.material.yield_stress,
            section_modulus_tension=self.profile.section.Sx,
            section_modulus_compression=self.profile.section.Sx,
        )
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=stress,
            factor=0.95,
            kc_coefficient=self.kc_coefficient,
        )

    @cached_property
    def flexural_non_compact_slender_limit(self):
        table = {
            ConstructionType.ROLLED: self.flexural_slender_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.flexural_slender_limit_ratio_built_up,
        }
        return table[self.profile.construction]

    @cached_property
    def flexural_minor_axis_slender_limit_ratio(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1,
        )

    @cached_property
    def axial(self):
        return axial_slenderness_per_element(
            limit=self.axial_limit,
            slenderness=self.ratio,
        )

    @cached_property
    def flexural_minor_axis(self):
        return flexural_slenderness_per_element(
            ratio=self.ratio,
            limit_slender=self.flexural_minor_axis_slender_limit_ratio,
            limit_compact=self.flexural_compact_non_compact_limit,
        )

    @cached_property
    def flexural_major_axis(self):
        return flexural_slenderness_per_element(
            ratio=self.ratio,
            limit_slender=self.flexural_non_compact_slender_limit,
            limit_compact=self.flexural_compact_non_compact_limit,
        )


@dataclass(frozen=True)
class DoublySymmetricIAISC36010:
    # dimensions: "DoublySymmetricIDimensions"
    section: AISC_Section
    material: IsotropicMaterial
    construction: ConstructionType = ConstructionType.ROLLED
    # coefficient_c: float = 1.0

    @cached_property
    def _flange_slenderness(self):
        return DoublySymmetricIFlangeSlenderness(profile=self)

    @cached_property
    def _web_slenderness(self):
        return DoublySymmetricIWebSlenderness(profile=self)

    @cached_property
    def slenderness(self):
        return DoublySymmetricIAndChannelSlenderness(
            web_axial=self._web_slenderness.axial,
            web_flexure_major_axis=self._web_slenderness.flexural_major_axis,
            flange_axial=self._flange_slenderness.axial,
            flange_flexure_major_axis=self._flange_slenderness.flexural_major_axis,
            flange_flexure_minor_axis=self._flange_slenderness.flexural_minor_axis,
        )

    @cached_property
    def slenderness_calc_memory(self):
        return DoublySymmetricIAndChannelSlendernessCalcMemory(
            axial=DoublySymmetricIAndChannelAxialCalcMemory(
                flange=AxialSlendernessCalcMemory(
                    ratio=self._flange_slenderness.ratio,
                    slender_limit=self._flange_slenderness.axial_limit,
                    value=self.slenderness.flange_axial,
                ),
                web=AxialSlendernessCalcMemory(
                    ratio=self._web_slenderness.ratio,
                    slender_limit=self._web_slenderness.axial_limit,
                    value=self.slenderness.web_axial,
                ),
            ),
            flexure_major_axis=DoublySymmetricIAndChannelFlexureMajorAxisCalcMemory(
                flange=FlexuralSlendernessCalcMemory(
                    ratio=self._flange_slenderness.ratio,
                    compact_non_compact_limit=self._flange_slenderness.flexural_compact_non_compact_limit,
                    non_compact_slender_limit=self._flange_slenderness.flexural_non_compact_slender_limit,
                    value=self._flange_slenderness.flexural_major_axis,
                ),
                web=FlexuralSlendernessCalcMemory(
                    ratio=self._web_slenderness.ratio,
                    compact_non_compact_limit=self._web_slenderness.flexural_compact_non_compact_limit,
                    non_compact_slender_limit=self._web_slenderness.flexural_non_compact_slender_limit,
                    value=self._flange_slenderness.flexural_major_axis,
                ),
            ),
            flexure_minor_axis=DoublySymmetricIAndChannelFlexureMinorAxisCalcMemory(
                flange=FlexuralSlendernessCalcMemory(
                    ratio=self._flange_slenderness.ratio,
                    compact_non_compact_limit=self._flange_slenderness.flexural_compact_non_compact_limit,
                    non_compact_slender_limit=self._flange_slenderness.flexural_non_compact_slender_limit,
                    value=self._flange_slenderness.flexural_major_axis,
                ),
            ),
        )

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
            axis=Axis.MINOR,
        )
        torsional_buckling_strength = TorsionalBucklingDoublySymmetricI(
            profile=self, length=length_torsion, factor_k=factor_k_torsion
        )
        return DesignStrength(
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis,
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis,
                StrengthType.TORSIONAL_BUCKLING: torsional_buckling_strength,
            }
        )

    @cached_property
    def flex_yield_major_axis(self) -> Strength:
        return MajorAxisFlexurePlasticYielding(self)

    @cached_property
    def flex_yield_minor_axis(self) -> Strength:
        return MinorAxisFlexurePlasticYielding(self)

    @cached_property
    def flex_major_axis_non_compact_flange_local_buckling(self):
        return NonCompactFlangeLocalBuckling(
            profile=self,
            axis=Axis.MAJOR
        )

    @cached_property
    def flex_major_axis_slender_flange_local_buckling(self):
        return SlenderFlangeLocalBuckingMajorAxis(
            profile=self,
        )

    @cached_property
    def flex_minor_axis_non_compact_flange_local_buckling(self):
        return NonCompactFlangeLocalBuckling(
            profile=self,
            axis=Axis.MINOR
        )

    def flexure_major_axis(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
    ) -> DesignStrength:
        nominal_strengths = {
            StrengthType.YIELD: self.flex_yield_major_axis,
            StrengthType.LATERAL_TORSIONAL_BUCKLING: LateralTorsionalBucklingDoublySymmetricI(
                profile=self,
                length=length,
                modification_factor=lateral_torsional_buckling_modification_factor,
            ),
        }
        if self.slenderness.flange_flexure_major_axis == Slenderness.NON_COMPACT:
            nominal_strengths.update(
                {StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING: self.flex_major_axis_non_compact_flange_local_buckling}
            )
        return DesignStrength(nominal_strengths=nominal_strengths)

    def flexure_minor_axis(
        self,
    ) -> DesignStrength:
        nominal_strengths = {
            StrengthType.YIELD: MinorAxisFlexurePlasticYielding(self)
        }
        if self.slenderness.flange_flexure_minor_axis == Slenderness.NON_COMPACT:
            nominal_strengths.update(
                {StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING: self.flex_minor_axis_non_compact_flange_local_buckling}
            )

        return DesignStrength(nominal_strengths=nominal_strengths)

    def shear_major_axis(self) -> DesignStrength:
        ...

    def shear_minor_axis(self) -> DesignStrength:
        ...


@dataclass(frozen=True)
class LateralTorsionalBucklingDoublySymmetricI(LateralTorsionalBuckling):
    @cached_property
    def coefficient_c(self) -> float:
        return 1


@dataclass(frozen=True)
class TorsionalBucklingDoublySymmetricI(BucklingStrengthMixin):
    profile: "DoublySymmetricIAISC36010"
    factor_k: float
    length: Quantity

    @cached_property
    def elastic_buckling_stress(self):
        return elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.profile.material.modulus_linear,
            factor_k=self.factor_k,
            length=self.length,
            major_axis_inertia=self.profile.section.Ix,
            minor_axis_inertia=self.profile.section.Iy,
            torsional_constant=self.profile.section.J,
            modulus_shear=self.profile.material.modulus_shear,
            warping_constant=self.profile.section.Cw,
        )

    @cached_property
    def detailed_results(self) -> dict[str, Quantity | float]:
        return {
            ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
            **super().detailed_results,
        }


# def create_doubly_symmetric_i(
#     dimensions: DoublySymmetricIDimensions,
#     material: IsotropicMaterial,
#     area_properties: AreaProperties = None,
#     construction: ConstructionType = ConstructionType.ROLLED,
# ) -> DoublySymmetricIAISC36010:
#     return DoublySymmetricIAISC36010(
#         dimensions=dimensions,
#         material=material,
#         area_properties=area_properties
#         or doubly_symmetric_i_area_properties(dimensions),
#         construction=construction,
#     )
