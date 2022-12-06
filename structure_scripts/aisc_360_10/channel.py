from dataclasses import dataclass
from functools import cached_property
from typing import Union, TYPE_CHECKING

from quantities import Quantity

from structure_scripts.aisc_360_10.compression import (
    FlexuralBucklingStrength,
    BucklingStrengthMixin,
    ELASTIC_BUCKLING_STRESS,
)
from structure_scripts.aisc_360_10.criteria import (
    DesignStrength,
    DesignType,
    StrengthType,
)
from structure_scripts.aisc_360_10.flexure import (
    MajorAxisFlexurePlasticYielding,
)
from structure_scripts.aisc_360_10.i_profile import (
    DoublySymmetricIFlangeSlenderness,
    DoublySymmetricIWebSlenderness,
    LateralTorsionalBucklingDoublySymmetricI,
)
from structure_scripts.aisc_360_10.section_slenderness import (
    DoublySymmetricIAndChannelSlenderness,
    DoublySymmetricIAndChannelSlendernessCalcMemory,
    DoublySymmetricIAndChannelAxialCalcMemory,
    AxialSlendernessCalcMemory,
    DoublySymmetricIAndChannelFlexureMajorAxisCalcMemory,
    FlexuralSlendernessCalcMemory,
    DoublySymmetricIAndChannelFlexureMinorAxisCalcMemory,
)
from structure_scripts.helpers import (
    rectangle_area,
    self_inertia,
    transfer_inertia,
    section_modulus,
    radius_of_gyration,
    areas_centroid,
    Axis,
    member_slenderness_ratio, _channel_area, factor_h,
)
from structure_scripts.materials import IsotropicMaterial

from structure_scripts.section_properties import (
    AreaProperties,
    ConstructionType,
)
from structure_scripts.aisc_360_10.helpers import (
    elastic_flexural_buckling_stress,
    elastic_buckling_stress_polar,
    elastic_bucking_stress_singly_symmetric,
)

if TYPE_CHECKING:
    from structure_scripts.sections import (
        ChannelDimensions,
    )


@dataclass(frozen=True)
class ChannelAISC36010:
    dimensions: "ChannelDimensions"
    material: IsotropicMaterial
    area_properties: AreaProperties
    construction: ConstructionType = ConstructionType.ROLLED
    # coefficient_c: float = 1.0

    @cached_property
    def _flange_slenderness(self):
        return DoublySymmetricIFlangeSlenderness(profile=self)

    @cached_property
    def _web_slenderness(self):
        return DoublySymmetricIWebSlenderness(section=self)

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
            section=self,
            length=length_major_axis,
            factor_k=factor_k_major_axis,
            axis=Axis.MAJOR,
        )
        flexural_buckling_minor_axis = FlexuralBucklingStrength(
            section=self,
            length=length_minor_axis,
            factor_k=factor_k_minor_axis,
            axis=Axis.MINOR,
        )
        torsional_buckling_strength = TorsionalBucklingDoublySinglySymmetric(
            section=self, length=length_torsion, factor_k=factor_k_torsion
        )
        return DesignStrength(
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis,
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis,
                StrengthType.TORSIONAL_BUCKLING: torsional_buckling_strength,
            }
        )

    def flexure_major_axis(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
    ) -> DesignStrength:
        return DesignStrength(
            nominal_strengths={
                StrengthType.YIELD: MajorAxisFlexurePlasticYielding(self),
                StrengthType.LATERAL_TORSIONAL_BUCKLING: LateralTorsionalBucklingDoublySymmetricI(
                    section=self,
                    length=length,
                    modification_factor=lateral_torsional_buckling_modification_factor,
                ),
            }
        )

    def flexure_minor_axis(
        self,
        length: Quantity,
        # lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> DesignStrength:
        ...

    def shear_major_axis(self) -> DesignStrength:
        ...

    def shear_minor_axis(self) -> DesignStrength:
        ...


@dataclass(frozen=True)
class TorsionalBucklingDoublySinglySymmetric(BucklingStrengthMixin):
    section: "ChannelAISC36010"
    factor_k: float
    length: Quantity
    symmetry_axis: Axis = Axis.MAJOR

    @cached_property
    def radius_of_gyration(self):
        table = {
            Axis.MAJOR: self.section.area_properties.major_axis_radius_of_gyration,
            Axis.MINOR: self.section.area_properties.minor_axis_radius_of_gyration,
        }
        return table[self.symmetry_axis]

    @cached_property
    def member_slenderness_ratio(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k,
            radius_of_gyration=self.radius_of_gyration,
            unbraced_length=self.length,
        )

    @cached_property
    def elastic_buckling_stress_symmetry_axis(self):
        return elastic_flexural_buckling_stress(
            modulus_linear=self.section.material.modulus_linear,
            member_slenderness_ratio=self.member_slenderness_ratio,
        )

    @cached_property
    def elastic_buckling_stress_polar(self):
        return elastic_buckling_stress_polar(
            modulus_linear=self.section.material.modulus_linear,
            modulus_shear=self.section.material.modulus_linear,
            warping_constant=self.section.area_properties.warping_constant,
            factor_k=self.factor_k,
            length=self.length,
            area=self.section.area_properties.area,
            polar_radius_of_gyration=self.section.area_properties.polar_radius_of_gyration,
            torsional_constant=self.section.area_properties.torsional_constant,
        )

    @cached_property
    def factor_h(self):
        return factor_h(
            major_axis_shear_centroid=self.section.area_properties.major_axis_shear_centroid,
            minor_axis_shear_centroid=self.section.area_properties.minor_axis_shear_centroid,
            polar_radius_of_gyration=self.section.area_properties.polar_radius_of_gyration
        )

    @cached_property
    def elastic_buckling_stress(self):
        return elastic_bucking_stress_singly_symmetric(
            elastic_buckling_stress_y=self.elastic_buckling_stress_symmetry_axis,
            elastic_buckling_stress_z=self.elastic_buckling_stress_polar,
            factor_h=self.factor_h,
        )

    @cached_property
    def detailed_results(self) -> dict[str, Quantity | float]:
        return {
            ELASTIC_BUCKLING_STRESS: self.elastic_buckling_stress,
            **super().detailed_results,
        }
