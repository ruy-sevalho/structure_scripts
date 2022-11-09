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
    Criteria,
    nominal_strength,
    LoadingStrength, DesignStrength,
)
from structure_scripts.aisc_360_10.helpers import (
    limit_ratio_default,
    kc_coefficient,
    limit_stress_built_up_sections,
    elastic_torsional_buckling_stress_doubly_symmetric_member,
)
from structure_scripts.aisc_360_10.sections import LoadReturn
from structure_scripts.aisc_360_10.section_slenderness import (
    # ElementSlenderness,
    # FlangeWebSlenderness,
    # FlexuralSlendernessCompute,
    axial_slenderness_per_element,
    flexural_slenderness_per_element,
    DoublySymmetricIAndChannelSlenderness,
    DoublySymmetricIAndChannelSlendernessCalcMemory,
    DoublySymmetricIAndChannelAxialCalcMemory,
    AxialSlendernessCalcMemory,
    FlexuralSlendernessCalcMemory,
    DoublySymmetricIAndChannelFlexureMajorAxisCalcMemory,
    DoublySymmetricIAndChannelFlexureMinorAxisCalcMemory,
)
from structure_scripts.helpers import (
    Axis,
)
from structure_scripts.materials import IsotropicMaterial
# from structure_scripts._sections import (
#     DoublySymmetricIDimensions,
#     doubly_symmetric_i_area_properties,
#     ConstructionType,
# )
from structure_scripts.section_properties import AreaProperties, ConstructionType

if TYPE_CHECKING:
    from structure_scripts.sections import DoublySymmetricI, DoublySymmetricIDimensions


# @dataclass
# class DoublySymmetricIFlangeWebSlenderness(FlangeWebSlenderness):
#     section: "DoublySymmetricI"
#
#     @cached_property
#     def flange(self):
#         return DoublySymmetricIFlangeSlenderness(profile=self.section)
#
#     @cached_property
#     def web(self):
#         return DoublySymmetricIWebSlenderness(profile=self.section)
#
#
# class DoublySymmetricIDimensions(Protocol):
#     flange_width: Quantity
#     flange_thickness: Quantity
#     web_height: Quantity
#     web_thickness: Quantity
#     total_height: Quantity
#     distance_between_centroids: Quantity
#     web_height_corrected: Quantity
#     web_radii: Quantity
#
#     def table(self, filter_names: list[str] = None):
#         return extract_input_dataframe(
#             obj=self,
#             extraction_type=DoublySymmetricIDimensions,
#             filter_names=filter_names,
#         )
#
#     @cached_property
#     def default_table(self):
#         return self.table()
#
#     @cached_property
#     def latex(self):
#         return DoublySymmetricIDimensionsLatex(self)


# @dataclass
# class DoublySymmetricIAreaPropertiesFromDimensions:
#     dimensions: DoublySymmetricIDimensions
#
#     @cached_property
#     def _flange_area(self):
#         return rectangle_area(
#             width=self.dimensions.flange_width,
#             height=self.dimensions.flange_thickness,
#         )
#
#     @cached_property
#     def _web_area(self):
#         return rectangle_area(
#             width=self.dimensions.web_thickness,
#             height=self.dimensions.web_height,
#         )
#
#     @cached_property
#     def area(self) -> Quantity:
#         return self._web_area + 2 * self._flange_area
#
#     @cached_property
#     def _flange_self_inertia_major_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.flange_width,
#             height=self.dimensions.flange_thickness,
#         )
#
#     @cached_property
#     def _flange_self_inertia_minor_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.flange_thickness,
#             height=self.dimensions.flange_width,
#         )
#
#     @cached_property
#     def _web_self_inertia_major_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.web_thickness,
#             height=self.dimensions.web_height,
#         )
#
#     @cached_property
#     def _web_self_inertia_minor_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.web_height,
#             height=self.dimensions.web_thickness,
#         )
#
#     @cached_property
#     def _flange_area_centroid_major_axis(self):
#         return self.dimensions.distance_between_centroids / 2
#
#     @cached_property
#     def _flange_transfer_inertia_major_axis(self):
#         return transfer_inertia(
#             area=self._flange_area,
#             center_to_na_distance=self._flange_area_centroid_major_axis,
#         )
#
#     @cached_property
#     def _minor_axis_inertia(self):
#         return (
#             2 * self._flange_self_inertia_minor_axis
#             + self._web_self_inertia_minor_axis
#         )
#
#     @cached_property
#     def _major_axis_inertia(self):
#         return (
#             2 * self._flange_transfer_inertia_major_axis
#             + 2 * self._flange_self_inertia_major_axis
#             + self._web_self_inertia_major_axis
#         )
#
#     @cached_property
#     def _major_axis_elastic_section_modulus(self) -> Quantity:
#         return section_modulus(
#             self._major_axis_inertia, self.dimensions.total_height / 2
#         )
#
#     @cached_property
#     def _minor_axis_elastic_section_modulus(self) -> Quantity:
#         return section_modulus(
#             self._minor_axis_inertia, self.dimensions.flange_width / 2
#         )
#
#     @cached_property
#     def _major_axis_radius_of_gyration(self) -> Quantity:
#         return radius_of_gyration(
#             moment_of_inertia=self._major_axis_inertia,
#             gross_section_area=self.area,
#         )
#
#     @cached_property
#     def _minor_axis_radius_of_gyration(self) -> Quantity:
#         return radius_of_gyration(
#             moment_of_inertia=self._minor_axis_inertia,
#             gross_section_area=self.area,
#         )
#
#     @cached_property
#     def _torsional_constant(self) -> Quantity:
#         return doubly_symmetric_i_torsional_constant(
#             flange_width=self.dimensions.flange_width,
#             total_height=self.dimensions.total_height,
#             flange_thickness=self.dimensions.flange_thickness,
#             web_thickness=self.dimensions.web_thickness,
#         )
#
#     @cached_property
#     def _torsional_radius_of_gyration(self):
#         return radius_of_gyration(
#             moment_of_inertia=self._torsional_constant,
#             gross_section_area=self.area,
#         )
#
#     @cached_property
#     def _major_axis_plastic_half_centroid(self) -> Quantity:
#         return areas_centroid(
#             (
#                 (self._flange_area, self._flange_area_centroid_major_axis),
#                 (self._web_area / 2, self.dimensions.web_height / 4),
#             )
#         )
#
#     @cached_property
#     def _major_axis_plastic_half_area(self) -> Quantity:
#         return self._flange_area + self._web_area / 2
#
#     @cached_property
#     def _major_axis_plastic_section_modulus(self):
#         return (
#             2
#             * self._major_axis_plastic_half_centroid
#             * self._major_axis_plastic_half_area
#         )
#
#     @cached_property
#     def _minor_axis_plastic_half_centroid(self) -> Quantity:
#         return areas_centroid(
#             (
#                 (self._flange_area, self.dimensions.flange_width / 4),
#                 (self._web_area / 2, self.dimensions.web_thickness / 4),
#             )
#         )
#
#     @cached_property
#     def _minor_axis_plastic_half_area(self) -> Quantity:
#         return self._flange_area + self._web_area / 2
#
#     @cached_property
#     def _minor_axis_plastic_section_modulus(self):
#         return (
#             2
#             * self._minor_axis_plastic_half_area
#             * self._minor_axis_plastic_half_centroid
#         )
#
#     @cached_property
#     def major_axis(self) -> AxisBending:
#         return AxisBendingData(
#             _inertia=self._major_axis_inertia,
#             _elastic_section_modulus=self._major_axis_elastic_section_modulus,
#             _plastic_section_modulus=self._major_axis_plastic_section_modulus,
#             _radius_of_gyration=self._major_axis_radius_of_gyration,
#         )
#
#     @cached_property
#     def minor_axis(self) -> AxisBending:
#         return AxisBendingData(
#             _inertia=self._minor_axis_inertia,
#             _elastic_section_modulus=self._minor_axis_elastic_section_modulus,
#             _plastic_section_modulus=self._minor_axis_plastic_section_modulus,
#             _radius_of_gyration=self._minor_axis_radius_of_gyration,
#         )
#
#     @cached_property
#     def torsion(self) -> Torsion:
#         return TorsionData(
#             _inertia=self._torsional_constant,
#             _radius_of_gyration=self._torsional_radius_of_gyration,
#         )
#
#     @cached_property
#     def warping_constant(self):
#         return warping_constant(
#             moment_of_inertia=self._minor_axis_inertia,
#             distance_between_flanges_centroid=self.dimensions.distance_between_centroids,
#         )


@dataclass
class DoublySymmetricIWebSlenderness:
    profile: "DoublySymmetricIAISC36010"

    @cached_property
    def ratio(self):
        return (
            self.profile.dimensions.web_height_corrected
            / self.profile.dimensions.web_thickness
        )

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

    # @cached_property
    # def flexural_minor_axis(self):
    #     return flexural_slenderness_per_element(
    #         ratio=self.ratio,
    #         limit_slender=self.flexural_non_compact_slender_limit,
    #         limit_compact=self.flexural_compact_non_compact_limit,
    #     )

    @cached_property
    def flexural_major_axis(self):
        return flexural_slenderness_per_element(
            ratio=self.ratio,
            limit_slender=self.flexural_non_compact_slender_limit,
            limit_compact=self.flexural_compact_non_compact_limit,
        )

    @cached_property
    def shear_area(self) -> Quantity:
        return (
            self.profile.dimensions.web_height
            * self.profile.dimensions.web_thickness
        )


@dataclass
class DoublySymmetricIFlangeSlenderness:
    profile: "DoublySymmetricIAISC36010"

    @cached_property
    def ratio(self):
        return (
            self.profile.dimensions.flange_width
            / 2
            / self.profile.dimensions.flange_thickness
        )

    @cached_property
    def kc_coefficient(self):
        return kc_coefficient(
            web_height=self.profile.dimensions.web_height_corrected,
            web_thickness=self.profile.dimensions.web_thickness,
        )

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
            section_modulus_tension=self.profile.area_properties.major_axis_elastic_section_modulus,
            section_modulus_compression=self.profile.area_properties.major_axis_elastic_section_modulus,
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

    @cached_property
    def shear_area(self):
        return (
            self.profile.dimensions.flange_width
            * self.profile.dimensions.flange_thickness
        )


@dataclass(frozen=True)
class DoublySymmetricIAISC36010:
    dimensions: "DoublySymmetricIDimensions"
    material: IsotropicMaterial
    area_properties: AreaProperties
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

    # @cached_property
    # def web_axial_compression_slenderness(self) -> Slenderness:
    #     return self._web_slenderness.axial
    #
    # @cached_property
    # def flange_axial_compression_slenderness(self) -> Slenderness:
    #     return self._flange_slenderness.axial_compression_value
    #
    # @cached_property
    # def web_flexure_major_axis_slenderness(self) -> Slenderness:
    #     return self._web_slenderness.flexural_major_axis
    #
    # @cached_property
    # def flange_flexure_major_axis_slenderness(self) -> Slenderness:
    #     return self._flange_slenderness.flexural_major_axis
    #
    # @cached_property
    # def web_flexure_minor_axis_slenderness(self) -> Slenderness:
    #     return self._web_slenderness.flexural_minor_axis
    #
    # @cached_property
    # def flange_flexure_minor_axis_slenderness(self):
    #     return self._flange_slenderness.flexural_minor_axis
    #
    # @cached_property
    # def axial_slenderness_calc_memory(
    #     self,
    # ) -> dict[str : Union[Quantity, float]]:
    #     return {
    #         f"web_{SLENDERNESS_LIMIT}": self._web_slenderness.axial_limit,
    #         f"flange_{SLENDERNESS_LIMIT}": self._flange_slenderness.axial_limit,
    #     }
    #
    # @cached_property
    # def flexure_major_axis_slenderness_calc_memory(
    #     self,
    # ) -> dict[str : Union[Quantity, float]]:
    #     return {
    #         f"web_{SLENDERNESS_COMPACT_NON_COMPACT_LIMIT}": self._web_slenderness.flexural_compact_non_compact_limit,
    #         f"web_{SLENDERNESS_NON_COMPACT_SLENDER_LIMIT}": self._web_slenderness.flexural_non_compact_slender_limit,
    #         f"flange_{SLENDERNESS_COMPACT_NON_COMPACT_LIMIT}": self._flange_slenderness.flexural_compact_limit_ratio,
    #         f"flange_{SLENDERNESS_NON_COMPACT_SLENDER_LIMIT}": self._flange_slenderness.flexural_major_axis_slender_limit_ratio,
    #     }
    #
    # @cached_property
    # def flexure_minor_axis_slenderness_calc_memory(
    #     self,
    # ) -> dict[str : Union[Quantity, float]]:
    #     return {
    #         "web": {
    #             SLENDERNESS_COMPACT_NON_COMPACT_LIMIT: self._web_slenderness.flexural_compact_non_compact_limit,
    #             SLENDERNESS_NON_COMPACT_SLENDER_LIMIT: self._web_slenderness.flexural_non_compact_slender_limit,
    #         },
    #         "flange": {
    #             SLENDERNESS_COMPACT_NON_COMPACT_LIMIT: self._flange_slenderness.flexural_compact_limit_ratio,
    #             SLENDERNESS_NON_COMPACT_SLENDER_LIMIT: self._flange_slenderness.flexural_minor_axis_slender_limit_ratio,
    #         },
    #     }

    def compression(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
        design_type: DesignType = DesignType.ASD,
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
        torsional_buckling_strength = TorsionalBucklingDoublySymmetricI(
            section=self, length=length_torsion, factor_k=factor_k_torsion
        )
        # nominal_strengths = {
        #     StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis.nominal_strength,
        #     StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis.nominal_strength,
        #     StrengthType.TORSIONAL_BUCKLING: torsional_buckling_strength.nominal_strength,
        # }
        # design_strength_value, design_strength_type = nominal_strength(
        #     nominal_strengths=nominal_strengths,
        #     design_type=design_type,
        #     criteria=Criteria(),
        # )
        # detailed_results = {
        #     StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis.detailed_results,
        #     StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis.detailed_results,
        #     StrengthType.TORSIONAL_BUCKLING: torsional_buckling_strength.detailed_results,
        # }
        return DesignStrength(
            nominal_strengths={
            StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis,
            StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis,
            StrengthType.TORSIONAL_BUCKLING: torsional_buckling_strength,
        }
        )
    # def compression_nominal_strengths(
    #     self,
    #     length_major_axis: Quantity,
    #     factor_k_major_axis: float = 1.0,
    #     length_minor_axis: Quantity = None,
    #     factor_k_minor_axis: float = 1.0,
    #     length_torsion: Quantity = None,
    #     factor_k_torsion: float = 1.0,
    #     detailed_results: bool = False,
    # ) -> LoadReturn:
    #     length_minor_axis = length_minor_axis or length_minor_axis
    #     length_torsion = length_major_axis or length_torsion
    #     flexural_buckling_major_axis = FlexuralBucklingStrength(
    #         section=self,
    #         length=length_major_axis,
    #         factor_k=factor_k_major_axis,
    #         axis=Axis.MAJOR,
    #     )
    #     flexural_buckling_minor_axis = FlexuralBucklingStrength(
    #         section=self,
    #         length=length_minor_axis,
    #         factor_k=factor_k_minor_axis,
    #         axis=Axis.MINOR,
    #     )
    #     torsional_buckling_strength = TorsionalBucklingDoublySymmetricI(
    #         section=self, length=length_torsion, factor_k=factor_k_torsion
    #     )
    #     if detailed_results:
    #         return {
    #             StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: (
    #                 flexural_buckling_major_axis.nominal_strength,
    #                 flexural_buckling_major_axis.detailed_results,
    #             ),
    #             StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: (
    #                 flexural_buckling_minor_axis.nominal_strength,
    #                 flexural_buckling_minor_axis.detailed_results,
    #             ),
    #             StrengthType.TORSIONAL_BUCKLING: (
    #                 torsional_buckling_strength.nominal_strength,
    #                 torsional_buckling_strength.detailed_results,
    #             ),
    #         }
    #     else:
    #         return {
    #             StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: flexural_buckling_major_axis.nominal_strength,
    #             StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: flexural_buckling_minor_axis.nominal_strength,
    #             StrengthType.TORSIONAL_BUCKLING: torsional_buckling_strength.nominal_strength,
    #         }

    def shear_major_axis_design_strength(
        self, design_type: DesignType = DesignType.ASD
    ) -> tuple[Quantity, StrengthType]:
        ...

    def shear_major_axis_nominal_strengths(
        self, detailed_results: bool = False
    ) -> LoadReturn:
        ...

    def shear_minor_axis_design_strength(
        self, design_type: DesignType = DesignType.ASD
    ) -> tuple[Quantity, StrengthType]:
        ...

    def shear_minor_axis_nominal_strengths(
        self, detailed_results: bool = False
    ) -> LoadReturn:
        ...

    def flexure_major_axis_design_strength(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> Quantity:
        ...

    def flexure_major_axis_nominal_strengths(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        detailed_results: bool = False,
    ) -> Quantity:
        ...

    def flexure_minor_axis_design_strength(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> Quantity:
        ...

    def flexure_minor_axis_nominal_strengths(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        detailed_results: bool = False,
    ) -> Quantity:
        ...

    # @cached_property
    # def default_table(self):
    #     dimensions_table = self.dimensions.default_table
    #     area_properties_table = self.area_properties.data_table_df
    #     extra_table = extract_input_dataframe(
    #         obj=self,
    #         extraction_type=DoublySymmetricI,
    #         filter_names=["dimensions", "area_properties", "material"]
    #     )
    #     warping_constant_table = pd.DataFrame({"warping_constant": [self.warping_constant]})
    #     return pd.concat((dimensions_table, area_properties_table, warping_constant_table, extra_table), axis=1)
    #
    # @cached_property
    # def web_shear_buckling_coefficient(self):
    #     return 5
    #
    # @cached_property
    # def web_shear_coefficient_limit_0(self):
    #     return _web_shear_coefficient_limit(
    #         factor=2.24,
    #         web_shear_buckling_coefficient=1.0,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )
    #
    # @cached_property
    # def web_shear_coefficient_limit_i(self):
    #     return _web_shear_coefficient_limit(
    #         factor=1.1,
    #         web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )
    #
    # @cached_property
    # def web_shear_coefficient_limit_ii(self):
    #     return _web_shear_coefficient_limit(
    #         factor=1.37,
    #         web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )
    #
    # @cached_property
    # def web_shear_coefficient_iii(self):
    #     return web_shear_coefficient_iii(
    #         shear_buckling_coefficient=self.web_shear_buckling_coefficient,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #         web_slenderness=self.slenderness.web.slenderness_ratio,
    #     )
    #
    # @cached_property
    # def web_shear_coefficient(self):
    #     if (
    #         self.slenderness.web.slenderness_ratio
    #         <= self.web_shear_coefficient_limit_0
    #     ):
    #         return 1.0
    #     if (
    #         self.slenderness.web.slenderness_ratio
    #         < self.web_shear_coefficient_limit_i
    #     ):
    #         return 1.0
    #     elif (
    #         self.slenderness.web.slenderness_ratio
    #         < self.web_shear_coefficient_limit_ii
    #     ):
    #         return (
    #             self.web_shear_coefficient_limit_i
    #             / self.slenderness.web.slenderness_ratio
    #         )
    #     else:
    #         return self.web_shear_coefficient_iii

    # @cached_property
    # def warping_constant(self):
    #     if self.area_properties.warping_constant:
    #         return self.area_properties.warping_constant
    #     return warping_constant(
    #         moment_of_inertia=self.area_properties.minor_axis.inertia,
    #         distance_between_flanges_centroid=self.dimensions.distance_between_centroids,
    #     )
    #
    # @cached_property
    # def effective_radius_of_gyration(self):
    #     return effective_radius_of_gyration(
    #         major_section_modulus=self.area_properties.major_axis.elastic_section_modulus,
    #         minor_inertia=self.area_properties.minor_axis.inertia,
    #         warping_constant=self.warping_constant,
    #     )
    #
    # @cached_property
    # def limit_length_torsional_buckling(self):
    #     return limiting_length_lateral_torsional_buckling(
    #         modulus=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #         section_modulus=self.area_properties.major_axis.elastic_section_modulus,
    #         torsional_constant=self.area_properties.torsion.inertia,
    #         effective_radius_of_gyration=self.effective_radius_of_gyration,
    #         distance_between_centroids=self.dimensions.distance_between_centroids,
    #         coefficient_c=self.coefficient_c,
    #     )
    #
    # @cached_property
    # def limit_length_yield(self):
    #     return limiting_length_yield(
    #         modulus=self.material.modulus_linear,
    #         radius_of_gyration=self.area_properties.minor_axis.radius_of_gyration,
    #         yield_stress=self.material.yield_stress,
    #     )

    # def elastic_torsional_buckling_stress(self, beam: "BeamAnalysis"):
    #     return elastic_torsional_buckling_stress_doubly_symmetric_member(
    #         modulus_linear=self.material.modulus_linear,
    #         modulus_shear=self.material.modulus_shear,
    #         factor_k=beam.parameters.factor_k_torsion,
    #         length=beam.parameters.unbraced_length_torsion,
    #         torsional_constant=self.area_properties.torsion.inertia,
    #         major_axis_inertia=self.area_properties.major_axis.inertia,
    #         minor_axis_inertia=self.area_properties.minor_axis.inertia,
    #         warping_constant=self.warping_constant,
    #     )

    # def torsional_buckling_critical_stress_effective_length(
    #     self, beam: "BeamAnalysis"
    # ):
    #     return critical_compression_stress_buckling_default(
    #         # member_slenderness=beam.torsion_slenderness,
    #         # member_slenderness_limit=beam.slenderness_limit,
    #         yield_stress=self.material.yield_stress,
    #         elastic_buckling_stress=self.elastic_torsional_buckling_stress(
    #             beam
    #         ),
    #     )


@dataclass(frozen=True)
class TorsionalBucklingDoublySymmetricI(BucklingStrengthMixin):
    section: "DoublySymmetricIAISC36010"
    factor_k: float
    length: Quantity

    @cached_property
    def elastic_buckling_stress(self):
        return elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.section.material.modulus_linear,
            factor_k=self.factor_k,
            length=self.length,
            major_axis_inertia=self.section.area_properties.major_axis_inertia,
            minor_axis_inertia=self.section.area_properties.minor_axis_inertia,
            torsional_constant=self.section.area_properties.polar_inertia,
            modulus_shear=self.section.material.modulus_shear,
            warping_constant=self.section.area_properties.warping_constant,
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
