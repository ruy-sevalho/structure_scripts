from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING, Optional

import pandas as pd
from quantities import Quantity

from structure_scripts.aisc_360_10.compression import (
    FLEXURAL_BUCKLING_MAJOR_AXIS_STRENGTH,
    FLEXURAL_BUCKLING_MINOR_AXIS_STRENGTH,
    FlexuralBuckling,
)
from structure_scripts.aisc_360_10.criteria import DesignStrength
from structure_scripts.aisc_360_10.sections import (
    SectionProfileWebFlangeTorsBuck,
)
from structure_scripts.aisc_360_10.elements_latex import (
    DoublySymmetricIDimensionsLatex,
    DoublySymmetricIUserDefinedLatex,
)
from structure_scripts.aisc_360_10.helpers import (
    warping_constant,
    doubly_symmetric_i_torsional_constant,
    web_height,
    limit_ratio_default,
    kc_coefficient,
    ConstructionType,
    limit_stress_built_up_sections,
    _web_shear_coefficient_limit,
    web_shear_coefficient_iii,
    effective_radius_of_gyration,
    limiting_length_lateral_torsional_buckling,
    limiting_length_yield,
    elastic_torsional_buckling_stress_doubly_symmetric_member,
    critical_compression_stress_buckling_default,
)
from structure_scripts.aisc_360_10.shear import (
    StandardShearMajorAxisCriteriaAdaptor,
    StandardShearCriteriaAdaptor,
    SHEAR_STRENGTH,
)
from structure_scripts.aisc_360_10.section_slenderness import (
    ElementSlenderness,
    FlangeWebSlenderness,
    Slenderness,
    flexural_slenderness_per_element,
    AxialSlendernessCompute,
    FlexuralSlendernessCompute,
)
from structure_scripts.shared.data import extract_input_dataframe
from structure_scripts.shared.helpers import (
    section_modulus,
    radius_of_gyration,
    self_inertia,
    transfer_inertia,
    rectangle_area,
    areas_centroid,
    ratio_simplify,
    Axis,
)
from structure_scripts.shared.materials import IsotropicMaterial
from structure_scripts.shared.sections import (
    AreaProperties,
    AxisBending,
    AxisBendingData,
    TorsionData,
    Torsion,
)

if TYPE_CHECKING:
    from structure_scripts.aisc_360_10.beams import BeamAnalysis, Beam


@dataclass
class DoublySymmetricIFlangeWebSlenderness(FlangeWebSlenderness):
    section: "DoublySymmetricI"

    @property
    def flange(self):
        return DoublySymmetricIFlangeSlenderness(profile=self.section)

    @property
    def web(self):
        return DoublySymmetricIWebSlenderness(profile=self.section)


class DoublySymmetricIDimensions(Protocol):
    flange_width: Quantity
    flange_thickness: Quantity
    web_height: Quantity
    web_thickness: Quantity
    total_height: Quantity
    distance_between_centroids: Quantity
    web_height_corrected: Quantity
    web_radii: Quantity

    def table(self, filter_names: list[str] = None):
        return extract_input_dataframe(
            obj=self,
            extraction_type=DoublySymmetricIDimensions,
            filter_names=filter_names,
        )

    @property
    def default_table(self):
        return self.table()

    @property
    def latex(self):
        return DoublySymmetricIDimensionsLatex(self)


@dataclass
class DoublySymmetricIAreaPropertiesCompute(AreaProperties):
    dimensions: DoublySymmetricIDimensions

    @property
    def _flange_area(self):
        return rectangle_area(
            width=self.dimensions.flange_width,
            height=self.dimensions.flange_thickness,
        )

    @property
    def web_area(self):
        return rectangle_area(
            width=self.dimensions.web_thickness,
            height=self.dimensions.web_height,
        )

    @property
    def area(self) -> Quantity:
        return self.web_area + 2 * self._flange_area

    @property
    def _flange_self_inertia_major_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.flange_width,
            height=self.dimensions.flange_thickness,
        )

    @property
    def _flange_self_inertia_minor_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.flange_thickness,
            height=self.dimensions.flange_width,
        )

    @property
    def _web_self_inertia_major_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.web_thickness,
            height=self.dimensions.web_height,
        )

    @property
    def _web_self_inertia_minor_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.web_height,
            height=self.dimensions.web_thickness,
        )

    @property
    def _flange_area_centroid_major_axis(self):
        return self.dimensions.distance_between_centroids / 2

    @property
    def _flange_transfer_inertia_major_axis(self):
        return transfer_inertia(
            area=self._flange_area,
            center_to_na_distance=self._flange_area_centroid_major_axis,
        )

    @property
    def minor_axis_inertia(self):
        return (
            2 * self._flange_self_inertia_minor_axis
            + self._web_self_inertia_minor_axis
        )

    @property
    def major_axis_inertia(self):
        return (
            2 * self._flange_transfer_inertia_major_axis
            + 2 * self._flange_self_inertia_major_axis
            + self._web_self_inertia_major_axis
        )

    @property
    def major_axis_elastic_section_modulus(self) -> Quantity:
        return section_modulus(
            self.major_axis_inertia, self.dimensions.total_height / 2
        )

    @property
    def minor_axis_elastic_section_modulus(self) -> Quantity:
        return section_modulus(
            self.minor_axis_inertia, self.dimensions.flange_width / 2
        )

    @property
    def major_axis_radius_of_gyration(self) -> Quantity:
        return radius_of_gyration(
            moment_of_inertia=self.major_axis_inertia,
            gross_section_area=self.area,
        )

    @property
    def minor_axis_radius_of_gyration(self) -> Quantity:
        return radius_of_gyration(
            moment_of_inertia=self.minor_axis_inertia,
            gross_section_area=self.area,
        )

    @property
    def warping_constant(self):
        return warping_constant(
            moment_of_inertia=self.minor_axis_inertia,
            distance_between_flanges_centroid=self.dimensions.distance_between_centroids,
        )

    @property
    def torsional_constant(self) -> Quantity:
        return doubly_symmetric_i_torsional_constant(
            flange_width=self.dimensions.flange_width,
            total_height=self.dimensions.total_height,
            flange_thickness=self.dimensions.flange_thickness,
            web_thickness=self.dimensions.web_thickness,
        )

    @property
    def torsional_radius_of_gyration(self):
        return radius_of_gyration(
            moment_of_inertia=self.torsional_constant,
            gross_section_area=self.area,
        )

    @property
    def _major_axis_plastic_half_centroid(self) -> Quantity:
        return areas_centroid(
            (
                (self._flange_area, self._flange_area_centroid_major_axis),
                (self.web_area / 2, self.dimensions.web_height / 4),
            )
        )

    @property
    def _major_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self.web_area / 2

    @property
    def major_axis_plastic_section_modulus(self):
        return (
            2
            * self._major_axis_plastic_half_centroid
            * self._major_axis_plastic_half_area
        )

    @property
    def _minor_axis_plastic_half_centroid(self) -> Quantity:
        return areas_centroid(
            (
                (self._flange_area, self.dimensions.flange_width / 4),
                (self.web_area / 2, self.dimensions.web_thickness / 4),
            )
        )

    @property
    def _minor_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self.web_area / 2

    @property
    def minor_axis_plastic_section_modulus(self):
        return (
            2
            * self._minor_axis_plastic_half_area
            * self._minor_axis_plastic_half_centroid
        )

    @property
    def major_axis(self) -> AxisBending:
        return AxisBendingData(
            inertia=self.major_axis_inertia,
            elastic_section_modulus=self.major_axis_elastic_section_modulus,
            plastic_section_modulus=self.major_axis_elastic_section_modulus,
            radius_of_gyration=self.major_axis_radius_of_gyration,
        )

    @property
    def minor_axis(self) -> AxisBending:
        return AxisBendingData(
            inertia=self.major_axis_inertia,
            elastic_section_modulus=self.major_axis_elastic_section_modulus,
            plastic_section_modulus=self.major_axis_elastic_section_modulus,
            radius_of_gyration=self.major_axis_radius_of_gyration,
        )

    @property
    def torsion(self) -> Torsion:
        return TorsionData(
            inertia=self.torsional_constant,
            radius_of_gyration=self.torsional_radius_of_gyration,
        )


@dataclass
class DoublySymmetricIAreaPropertiesFromDimensions(AreaProperties):
    dimensions: DoublySymmetricIDimensions

    @property
    def _flange_area(self):
        return rectangle_area(
            width=self.dimensions.flange_width,
            height=self.dimensions.flange_thickness,
        )

    @property
    def _web_area(self):
        return rectangle_area(
            width=self.dimensions.web_thickness,
            height=self.dimensions.web_height,
        )

    @property
    def area(self) -> Quantity:
        return self._web_area + 2 * self._flange_area

    @property
    def _flange_self_inertia_major_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.flange_width,
            height=self.dimensions.flange_thickness,
        )

    @property
    def _flange_self_inertia_minor_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.flange_thickness,
            height=self.dimensions.flange_width,
        )

    @property
    def _web_self_inertia_major_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.web_thickness,
            height=self.dimensions.web_height,
        )

    @property
    def _web_self_inertia_minor_axis(self) -> Quantity:
        return self_inertia(
            width=self.dimensions.web_height,
            height=self.dimensions.web_thickness,
        )

    @property
    def _flange_area_centroid_major_axis(self):
        return self.dimensions.distance_between_centroids / 2

    @property
    def _flange_transfer_inertia_major_axis(self):
        return transfer_inertia(
            area=self._flange_area,
            center_to_na_distance=self._flange_area_centroid_major_axis,
        )

    @property
    def _minor_axis_inertia(self):
        return (
            2 * self._flange_self_inertia_minor_axis
            + self._web_self_inertia_minor_axis
        )

    @property
    def _major_axis_inertia(self):
        return (
            2 * self._flange_transfer_inertia_major_axis
            + 2 * self._flange_self_inertia_major_axis
            + self._web_self_inertia_major_axis
        )

    @property
    def _major_axis_elastic_section_modulus(self) -> Quantity:
        return section_modulus(
            self._major_axis_inertia, self.dimensions.total_height / 2
        )

    @property
    def _minor_axis_elastic_section_modulus(self) -> Quantity:
        return section_modulus(
            self._minor_axis_inertia, self.dimensions.flange_width / 2
        )

    @property
    def _major_axis_radius_of_gyration(self) -> Quantity:
        return radius_of_gyration(
            moment_of_inertia=self._major_axis_inertia,
            gross_section_area=self.area,
        )

    @property
    def _minor_axis_radius_of_gyration(self) -> Quantity:
        return radius_of_gyration(
            moment_of_inertia=self._minor_axis_inertia,
            gross_section_area=self.area,
        )

    @property
    def _torsional_constant(self) -> Quantity:
        return doubly_symmetric_i_torsional_constant(
            flange_width=self.dimensions.flange_width,
            total_height=self.dimensions.total_height,
            flange_thickness=self.dimensions.flange_thickness,
            web_thickness=self.dimensions.web_thickness,
        )

    @property
    def _torsional_radius_of_gyration(self):
        return radius_of_gyration(
            moment_of_inertia=self._torsional_constant,
            gross_section_area=self.area,
        )

    @property
    def _major_axis_plastic_half_centroid(self) -> Quantity:
        return areas_centroid(
            (
                (self._flange_area, self._flange_area_centroid_major_axis),
                (self._web_area / 2, self.dimensions.web_height / 4),
            )
        )

    @property
    def _major_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self._web_area / 2

    @property
    def _major_axis_plastic_section_modulus(self):
        return (
            2
            * self._major_axis_plastic_half_centroid
            * self._major_axis_plastic_half_area
        )

    @property
    def _minor_axis_plastic_half_centroid(self) -> Quantity:
        return areas_centroid(
            (
                (self._flange_area, self.dimensions.flange_width / 4),
                (self._web_area / 2, self.dimensions.web_thickness / 4),
            )
        )

    @property
    def _minor_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self._web_area / 2

    @property
    def _minor_axis_plastic_section_modulus(self):
        return (
            2
            * self._minor_axis_plastic_half_area
            * self._minor_axis_plastic_half_centroid
        )

    @property
    def major_axis(self) -> AxisBending:
        return AxisBendingData(
            inertia=self._major_axis_inertia,
            elastic_section_modulus=self._major_axis_elastic_section_modulus,
            plastic_section_modulus=self._major_axis_plastic_section_modulus,
            radius_of_gyration=self._major_axis_radius_of_gyration,
        )

    @property
    def minor_axis(self) -> AxisBending:
        return AxisBendingData(
            inertia=self._minor_axis_inertia,
            elastic_section_modulus=self._minor_axis_elastic_section_modulus,
            plastic_section_modulus=self._minor_axis_plastic_section_modulus,
            radius_of_gyration=self._minor_axis_radius_of_gyration,
        )

    @property
    def torsion(self) -> Torsion:
        return TorsionData(
            inertia=self._torsional_constant,
            radius_of_gyration=self._torsional_radius_of_gyration,
        )

    @property
    def warping_constant(self):
        return warping_constant(
            moment_of_inertia=self._minor_axis_inertia,
            distance_between_flanges_centroid=self.dimensions.distance_between_centroids,
        )


@dataclass
class DoublySymmetricIDimensionsUserDefined(DoublySymmetricIDimensions):
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
    area_properties: AreaProperties = None
    construction: ConstructionType = ConstructionType.ROLLED
    # coefficient_c: float = 1.0

    def __post_init__(self):
        if not self.area_properties:
            self.area_properties = (
                DoublySymmetricIAreaPropertiesFromDimensions(self.dimensions)
            )

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

    def compression(self, beam: "Beam") -> DesignStrength:
        return DesignStrength(
            strengths={
                FLEXURAL_BUCKLING_MAJOR_AXIS_STRENGTH: FlexuralBuckling(
                    section=self,
                    beam=beam,
                    axis=Axis.MAJOR,
                ),
                FLEXURAL_BUCKLING_MINOR_AXIS_STRENGTH: FlexuralBuckling(
                    section=self,
                    beam=beam,
                    axis=Axis.MINOR,
                ),
            }
        )
        # return {
        #     f"{FLEXURAL_BUCKLING}_major": create_compression_flexural_buckling_criteria(
        #         beam_param=beam_param, section=self, axis="major"
        #     ),
        #     f"{FLEXURAL_BUCKLING}_minor": create_compression_flexural_buckling_criteria(
        #         beam_param=beam_param, section=self, axis="minor"
        #     ),
        # }

    def shear_major_axis(self, beam: "Beam") -> DesignStrength:
        return {
            SHEAR_STRENGTH: StandardShearCriteriaAdaptor(
                beam=beam, section=self, axis=Axis.MAJOR
            ),
        }
