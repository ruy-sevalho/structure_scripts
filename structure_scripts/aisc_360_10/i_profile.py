from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    DesignType,
    StrengthType,
)

from structure_scripts.aisc_360_10.helpers import (
    warping_constant,
    doubly_symmetric_i_torsional_constant,
    web_height,
    limit_ratio_default,
    kc_coefficient,
    ConstructionType,
    limit_stress_built_up_sections,
)
from structure_scripts.aisc_360_10.sections import LoadReturn
from structure_scripts.aisc_360_10.section_slenderness import (
    ElementSlenderness,
    FlangeWebSlenderness,
    Slenderness,
    FlexuralSlendernessCompute,
)
from structure_scripts.helpers import (
    section_modulus,
    radius_of_gyration,
    self_inertia,
    transfer_inertia,
    rectangle_area,
    areas_centroid,
    ratio_simplify,
)
from structure_scripts.materials import IsotropicMaterial
from structure_scripts.sections import (
    SectionGeoProperties,
    TwoAxisData,
    ThreeAxisData,
)

if TYPE_CHECKING:
    pass


# @dataclass
# class DoublySymmetricIFlangeWebSlenderness(FlangeWebSlenderness):
#     section: "DoublySymmetricI"
#
#     @property
#     def flange(self):
#         return DoublySymmetricIFlangeSlenderness(profile=self.section)
#
#     @property
#     def web(self):
#         return DoublySymmetricIWebSlenderness(profile=self.section)


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
#     @property
#     def default_table(self):
#         return self.table()
#
#     @property
#     def latex(self):
#         return DoublySymmetricIDimensionsLatex(self)


@dataclass
class DoublySymmetricIDimensions:
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Quantity
    web_radii: Quantity = Quantity(0, "mm")

    @property
    def web_height(self):
        return web_height(self.total_height, self.flange_thickness)

    @property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness

    @property
    def web_height_corrected(self):
        if self.web_radii:
            return self.web_height - 2 * self.web_radii
        else:
            return self.web_height


def doubly_symmetric_i_section_properties(
    dimensions: DoublySymmetricIDimensions,
):
    flange_area = rectangle_area(
        width=dimensions.flange_width,
        height=dimensions.flange_thickness,
    )
    web_area = rectangle_area(
        width=dimensions.web_thickness,
        height=dimensions.web_height,
    )
    area = web_area + 2 * flange_area
    flange_self_inertia_major_axis = self_inertia(
        width=dimensions.flange_width,
        height=dimensions.flange_thickness,
    )
    flange_self_inertia_minor_axis = self_inertia(
        width=dimensions.flange_thickness,
        height=dimensions.flange_width,
    )
    web_self_inertia_major_axis = self_inertia(
        width=dimensions.web_thickness,
        height=dimensions.web_height,
    )
    web_self_inertia_minor_axis = self_inertia(
        width=dimensions.web_height,
        height=dimensions.web_thickness,
    )
    flange_area_centroid_major_axis = dimensions.distance_between_centroids / 2
    flange_transfer_inertia_major_axis = transfer_inertia(
        area=flange_area,
        center_to_na_distance=flange_area_centroid_major_axis,
    )
    minor_axis_inertia = (
        2 * flange_self_inertia_minor_axis + web_self_inertia_minor_axis
    )
    major_axis_inertia = (
        2 * flange_transfer_inertia_major_axis
        + 2 * flange_self_inertia_major_axis
        + web_self_inertia_major_axis
    )
    major_axis_elastic_section_modulus = section_modulus(
        major_axis_inertia, dimensions.total_height / 2
    )
    minor_axis_elastic_section_modulus = section_modulus(
        minor_axis_inertia, dimensions.flange_width / 2
    )
    major_axis_radius_of_gyration = radius_of_gyration(
        moment_of_inertia=major_axis_inertia,
        gross_section_area=area,
    )
    minor_axis_radius_of_gyration = radius_of_gyration(
        moment_of_inertia=minor_axis_inertia,
        gross_section_area=area,
    )
    polar_inertia = doubly_symmetric_i_torsional_constant(
        flange_width=dimensions.flange_width,
        total_height=dimensions.total_height,
        flange_thickness=dimensions.flange_thickness,
        web_thickness=dimensions.web_thickness,
    )
    torsional_radius_of_gyration = radius_of_gyration(
        moment_of_inertia=polar_inertia,
        gross_section_area=area,
    )
    major_axis_plastic_half_centroid = areas_centroid(
        (
            (flange_area, flange_area_centroid_major_axis),
            (web_area / 2, dimensions.web_height / 4),
        )
    )
    major_axis_plastic_half_area = flange_area + web_area / 2
    major_axis_plastic_section_modulus = (
        2 * major_axis_plastic_half_centroid * major_axis_plastic_half_area
    )
    minor_axis_plastic_half_centroid = areas_centroid(
        (
            (flange_area, dimensions.flange_width / 4),
            (web_area / 2, dimensions.web_thickness / 4),
        )
    )
    minor_axis_plastic_half_area = flange_area + web_area / 2
    minor_axis_plastic_section_modulus = (
        2 * minor_axis_plastic_half_area * minor_axis_plastic_half_centroid
    )
    return SectionGeoProperties(
        area=area,
        warping_constant=warping_constant(
            moment_of_inertia=minor_axis_inertia,
            distance_between_flanges_centroid=dimensions.distance_between_centroids,
        ),
        inertia=ThreeAxisData(
            major_axis=major_axis_inertia,
            minor_axis=minor_axis_inertia,
            torsion=polar_inertia,
        ),
        elastic_section_modulus=TwoAxisData(
            major_axis=major_axis_elastic_section_modulus,
            minor_axis=minor_axis_elastic_section_modulus,
        ),
        plastic_section_modulus=TwoAxisData(
            major_axis=major_axis_plastic_section_modulus,
            minor_axis=minor_axis_plastic_section_modulus,
        ),
        radius_of_gyration=ThreeAxisData(
            major_axis=major_axis_radius_of_gyration,
            minor_axis=minor_axis_radius_of_gyration,
            torsion=torsional_radius_of_gyration,
        ),
    )


# @dataclass
# class DoublySymmetricIAreaPropertiesFromDimensions:
#     dimensions: DoublySymmetricIDimensions
#
#     @property
#     def _flange_area(self):
#         return rectangle_area(
#             width=self.dimensions.flange_width,
#             height=self.dimensions.flange_thickness,
#         )
#
#     @property
#     def _web_area(self):
#         return rectangle_area(
#             width=self.dimensions.web_thickness,
#             height=self.dimensions.web_height,
#         )
#
#     @property
#     def area(self) -> Quantity:
#         return self._web_area + 2 * self._flange_area
#
#     @property
#     def _flange_self_inertia_major_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.flange_width,
#             height=self.dimensions.flange_thickness,
#         )
#
#     @property
#     def _flange_self_inertia_minor_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.flange_thickness,
#             height=self.dimensions.flange_width,
#         )
#
#     @property
#     def _web_self_inertia_major_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.web_thickness,
#             height=self.dimensions.web_height,
#         )
#
#     @property
#     def _web_self_inertia_minor_axis(self) -> Quantity:
#         return self_inertia(
#             width=self.dimensions.web_height,
#             height=self.dimensions.web_thickness,
#         )
#
#     @property
#     def _flange_area_centroid_major_axis(self):
#         return self.dimensions.distance_between_centroids / 2
#
#     @property
#     def _flange_transfer_inertia_major_axis(self):
#         return transfer_inertia(
#             area=self._flange_area,
#             center_to_na_distance=self._flange_area_centroid_major_axis,
#         )
#
#     @property
#     def _minor_axis_inertia(self):
#         return (
#             2 * self._flange_self_inertia_minor_axis
#             + self._web_self_inertia_minor_axis
#         )
#
#     @property
#     def _major_axis_inertia(self):
#         return (
#             2 * self._flange_transfer_inertia_major_axis
#             + 2 * self._flange_self_inertia_major_axis
#             + self._web_self_inertia_major_axis
#         )
#
#     @property
#     def _major_axis_elastic_section_modulus(self) -> Quantity:
#         return section_modulus(
#             self._major_axis_inertia, self.dimensions.total_height / 2
#         )
#
#     @property
#     def _minor_axis_elastic_section_modulus(self) -> Quantity:
#         return section_modulus(
#             self._minor_axis_inertia, self.dimensions.flange_width / 2
#         )
#
#     @property
#     def _major_axis_radius_of_gyration(self) -> Quantity:
#         return radius_of_gyration(
#             moment_of_inertia=self._major_axis_inertia,
#             gross_section_area=self.area,
#         )
#
#     @property
#     def _minor_axis_radius_of_gyration(self) -> Quantity:
#         return radius_of_gyration(
#             moment_of_inertia=self._minor_axis_inertia,
#             gross_section_area=self.area,
#         )
#
#     @property
#     def _torsional_constant(self) -> Quantity:
#         return doubly_symmetric_i_torsional_constant(
#             flange_width=self.dimensions.flange_width,
#             total_height=self.dimensions.total_height,
#             flange_thickness=self.dimensions.flange_thickness,
#             web_thickness=self.dimensions.web_thickness,
#         )
#
#     @property
#     def _torsional_radius_of_gyration(self):
#         return radius_of_gyration(
#             moment_of_inertia=self._torsional_constant,
#             gross_section_area=self.area,
#         )
#
#     @property
#     def _major_axis_plastic_half_centroid(self) -> Quantity:
#         return areas_centroid(
#             (
#                 (self._flange_area, self._flange_area_centroid_major_axis),
#                 (self._web_area / 2, self.dimensions.web_height / 4),
#             )
#         )
#
#     @property
#     def _major_axis_plastic_half_area(self) -> Quantity:
#         return self._flange_area + self._web_area / 2
#
#     @property
#     def _major_axis_plastic_section_modulus(self):
#         return (
#             2
#             * self._major_axis_plastic_half_centroid
#             * self._major_axis_plastic_half_area
#         )
#
#     @property
#     def _minor_axis_plastic_half_centroid(self) -> Quantity:
#         return areas_centroid(
#             (
#                 (self._flange_area, self.dimensions.flange_width / 4),
#                 (self._web_area / 2, self.dimensions.web_thickness / 4),
#             )
#         )
#
#     @property
#     def _minor_axis_plastic_half_area(self) -> Quantity:
#         return self._flange_area + self._web_area / 2
#
#     @property
#     def _minor_axis_plastic_section_modulus(self):
#         return (
#             2
#             * self._minor_axis_plastic_half_area
#             * self._minor_axis_plastic_half_centroid
#         )
#
#     @property
#     def major_axis(self) -> AxisBending:
#         return AxisBendingData(
#             _inertia=self._major_axis_inertia,
#             _elastic_section_modulus=self._major_axis_elastic_section_modulus,
#             _plastic_section_modulus=self._major_axis_plastic_section_modulus,
#             _radius_of_gyration=self._major_axis_radius_of_gyration,
#         )
#
#     @property
#     def minor_axis(self) -> AxisBending:
#         return AxisBendingData(
#             _inertia=self._minor_axis_inertia,
#             _elastic_section_modulus=self._minor_axis_elastic_section_modulus,
#             _plastic_section_modulus=self._minor_axis_plastic_section_modulus,
#             _radius_of_gyration=self._minor_axis_radius_of_gyration,
#         )
#
#     @property
#     def torsion(self) -> Torsion:
#         return TorsionData(
#             _inertia=self._torsional_constant,
#             _radius_of_gyration=self._torsional_radius_of_gyration,
#         )
#
#     @property
#     def warping_constant(self):
#         return warping_constant(
#             moment_of_inertia=self._minor_axis_inertia,
#             distance_between_flanges_centroid=self.dimensions.distance_between_centroids,
#         )


@dataclass
class DoublySymmetricIWebSlenderness(ElementSlenderness):
    profile: "DoublySymmetricI"

    @property
    def axial_compression_limit_ratio(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.49,
        )

    @property
    def slenderness_ratio(self) -> float:
        return ratio_simplify(
            self.profile.dimensions.web_height_corrected,
            self.profile.dimensions.web_thickness,
        )

    @property
    def flexural_compact_limit_ratio(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=3.76,
        )

    @property
    def flexural_slender_limit_ratio(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=5.7,
        )

    @property
    def axial_compression(self):
        return AxialSlendernessCompute(
            limit_ratio=self.axial_compression_limit_ratio,
            slenderness_ratio=self.slenderness_ratio,
        )

    @property
    def flexural_minor_axis(self):
        return FlexuralSlendernessCompute(
            slenderness_ratio=self.slenderness_ratio,
            slender_limit_ratio=self.flexural_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio,
        )

    @property
    def flexural_major_axis(self):
        return FlexuralSlendernessCompute(
            slenderness_ratio=self.slenderness_ratio,
            slender_limit_ratio=self.flexural_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio,
        )

    @property
    def shear_area(self) -> Quantity:
        return (
            self.profile.dimensions.web_height
            * self.profile.dimensions.web_thickness
        )

def doubly_symmetric_i_flange_slenderness():
    return

@dataclass
class DoublySymmetricIFlangeSlenderness(ElementSlenderness):
    profile: "DoublySymmetricI"

    @property
    def kc_coefficient(self):
        return kc_coefficient(
            web_height=self.profile.dimensions.web_height_corrected,
            web_thickness=self.profile.dimensions.web_thickness,
        )

    @property
    def axial_limit_ratio_rolled(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.56,
        )

    @property
    def axial_limit_ratio_built_up(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.64,
            kc_coefficient=self.kc_coefficient,
        )

    @property
    def axial_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.axial_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.axial_limit_ratio_built_up,
        }
        return table[self.profile.construction]

    @property
    def slenderness_ratio(self) -> float:
        return (
            self.profile.dimensions.flange_width
            / 2
            / self.profile.dimensions.flange_thickness
        )

    @property
    def axial_compression_value(self):
        limit = self.axial_limit_ratio
        ratio = self.ratio
        if ratio < limit:
            return Slenderness.NON_SLENDER
        return Slenderness.SLENDER

    @property
    def flexural_compact_limit_ratio(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.38,
        )

    @property
    def flexural_slender_limit_ratio_rolled(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.0,
        )

    @property
    def flexural_slender_limit_ratio_built_up(self):
        stress = limit_stress_built_up_sections(
            yield_stress=self.profile.material.yield_stress,
            section_modulus_tension=self.profile.area_properties.major_axis.elastic_section_modulus,
            section_modulus_compression=self.profile.area_properties.major_axis.elastic_section_modulus,
        )
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=stress,
            factor=0.95,
            kc_coefficient=self.kc_coefficient,
        )

    @property
    def flexural_major_axis_slender_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.flexural_slender_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.flexural_slender_limit_ratio_built_up,
        }
        return table[self.profile.construction]

    @property
    def flexural_minor_axis_slender_limit_ratio(self):
        return limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1,
        )

    @property
    def axial_compression(self):
        return AxialSlendernessCompute(
            limit_ratio=self.axial_limit_ratio,
            slenderness_ratio=self.slenderness_ratio,
        )

    @property
    def flexural_minor_axis(self):
        return FlexuralSlendernessCompute(
            ratio=self.ratio,
            slender_limit_ratio=self.flexural_minor_axis_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio,
        )

    @property
    def flexural_major_axis(self):
        return FlexuralSlendernessCompute(
            ratio=self.ratio,
            slender_limit_ratio=self.flexural_major_axis_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio,
        )

    @property
    def shear_area(self):
        return (
            self.profile.dimensions.flange_width
            * self.profile.dimensions.flange_thickness
        )


@dataclass
class DoublySymmetricI:
    dimensions: DoublySymmetricIDimensions
    material: IsotropicMaterial
    geo_properties: SectionGeoProperties = None
    construction: ConstructionType = ConstructionType.ROLLED
    # coefficient_c: float = 1.0

    @property
    def geo_properties(self) -> SectionGeoProperties:
        return (
            self._geo_properties
            or doubly_symmetric_i_section_properties(self.dimensions)
        )

    @geo_properties.setter
    def geo_properties(self, value: Union[SectionGeoProperties, None]) -> None:
        self._geo_properties = value


    # @property
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
    # @property
    # def web_shear_buckling_coefficient(self):
    #     return 5
    #
    # @property
    # def web_shear_coefficient_limit_0(self):
    #     return _web_shear_coefficient_limit(
    #         factor=2.24,
    #         web_shear_buckling_coefficient=1.0,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )
    #
    # @property
    # def web_shear_coefficient_limit_i(self):
    #     return _web_shear_coefficient_limit(
    #         factor=1.1,
    #         web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )
    #
    # @property
    # def web_shear_coefficient_limit_ii(self):
    #     return _web_shear_coefficient_limit(
    #         factor=1.37,
    #         web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )
    #
    # @property
    # def web_shear_coefficient_iii(self):
    #     return web_shear_coefficient_iii(
    #         shear_buckling_coefficient=self.web_shear_buckling_coefficient,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #         web_slenderness=self.slenderness.web.slenderness_ratio,
    #     )
    #
    # @property
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

    # @property
    # def warping_constant(self):
    #     if self.area_properties.warping_constant:
    #         return self.area_properties.warping_constant
    #     return warping_constant(
    #         moment_of_inertia=self.area_properties.minor_axis.inertia,
    #         distance_between_flanges_centroid=self.dimensions.distance_between_centroids,
    #     )
    #
    # @property
    # def effective_radius_of_gyration(self):
    #     return effective_radius_of_gyration(
    #         major_section_modulus=self.area_properties.major_axis.elastic_section_modulus,
    #         minor_inertia=self.area_properties.minor_axis.inertia,
    #         warping_constant=self.warping_constant,
    #     )
    #
    # @property
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
    # @property
    # def limit_length_yield(self):
    #     return limiting_length_yield(
    #         modulus=self.material.modulus_linear,
    #         radius_of_gyration=self.area_properties.minor_axis.radius_of_gyration,
    #         yield_stress=self.material.yield_stress,
    #     )

    @property
    def slenderness(self):
        return DoublySymmetricIFlangeWebSlenderness(section=self)

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

    def compression_design_strength(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> tuple[Quantity, StrengthType]:
        ...

    def compression_nominal_strengths(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
        detailed_results: bool = False,
        # design_type: DesignType = DesignType.ASD,
    ) -> LoadReturn:
        ...

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
