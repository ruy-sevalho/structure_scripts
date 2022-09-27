from dataclasses import dataclass
from functools import cached_property
from typing import Protocol, TYPE_CHECKING, Optional

import pandas as pd
from quantities import Quantity

from structure_scripts.aisc_360_10.elements_latex import DoublySymmetricIDimensionsLatex, \
    DoublySymmetricIUserDefinedLatex
from structure_scripts.aisc_360_10.helpers import Slenderness, _rectangle_area, _self_inertia, _transfer_inertia, \
    _radius_of_gyration, _warping_constant, _doubly_symmetric_i_torsional_constant, _areas_centroid, _web_height, \
    _limit_ratio_default, _flexural_slenderness_per_element, _kc_coefficient, ConstructionType, \
    _limit_stress_built_up_sections, _web_shear_coefficient_limit, _web_shear_coefficient_iii, \
    _effective_radius_of_gyration, _limiting_length_torsional_buckling, _limiting_length_yield, \
    _elastic_torsional_buckling_stress_doubly_symmetric_member, _critical_compression_stress_buckling_default
from structure_scripts.aisc_360_10.slenderness import AxialSlenderness, AxialSlendernessImplementation, \
    FlexuralSlenderness, FlexuralSlendernessImplementation, ElementSlenderness, FlangeWebSectionSlenderness
from structure_scripts.shared.data import extract_input_dataframe
from structure_scripts.shared.helpers import section_modulus
from structure_scripts.shared.materials import Material


if TYPE_CHECKING:
    from structure_scripts.aisc_360_10.sections import AreaPropertiesWithWeb


@dataclass
class DoublySymmetricIFlangeWebSectionSlenderness(FlangeWebSectionSlenderness):
    profile: "DoublySymmetricI"

    @cached_property
    def flange(self):
        return DoublySymmetricIFlangeSlenderness(profile=self.profile)

    @cached_property
    def web(self):
        return DoublySymmetricIWebSlenderness(profile=self.profile)


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
        return extract_input_dataframe(obj=self, extraction_type=DoublySymmetricIDimensions, filter_names=filter_names)

    @cached_property
    def default_table(self):
        return self.table()

    @cached_property
    def latex(self):
        return DoublySymmetricIDimensionsLatex(self)


@dataclass
class DoublySymmetricIAreaPropertiesFromDimensions:
    dimensions: DoublySymmetricIDimensions

    @cached_property
    def _flange_area(self):
        return _rectangle_area(width=self.dimensions.flange_width, height=self.dimensions.flange_thickness)

    @cached_property
    def web_area(self):
        return _rectangle_area(width=self.dimensions.web_thickness, height=self.dimensions.web_height)

    @cached_property
    def area(self) -> Quantity:
        return self.web_area + 2 * self._flange_area

    @cached_property
    def _flange_self_inertia_major_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.flange_width, height=self.dimensions.flange_thickness)

    @cached_property
    def _flange_self_inertia_minor_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.flange_thickness, height=self.dimensions.flange_width)

    @cached_property
    def _web_self_inertia_major_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.web_thickness, height=self.dimensions.web_height)

    @cached_property
    def _web_self_inertia_minor_axis(self) -> Quantity:
        return _self_inertia(width=self.dimensions.web_height, height=self.dimensions.web_thickness)

    @cached_property
    def _flange_area_centroid_major_axis(self):
        return self.dimensions.distance_between_centroids / 2

    @cached_property
    def _flange_transfer_inertia_major_axis(self):
        return _transfer_inertia(
            area=self._flange_area,
            center_to_na_distance=self._flange_area_centroid_major_axis
        )

    @cached_property
    def minor_axis_inertia(self):
        return 2 * self._flange_self_inertia_minor_axis + self._web_self_inertia_minor_axis

    @cached_property
    def major_axis_inertia(self):
        return 2 * self._flange_transfer_inertia_major_axis + 2 * self._flange_self_inertia_major_axis + \
               self._web_self_inertia_major_axis

    @cached_property
    def major_axis_elastic_section_modulus(self) -> Quantity:
        return section_modulus(self.major_axis_inertia, self.dimensions.total_height / 2)

    @cached_property
    def minor_axis_elastic_section_modulus(self) -> Quantity:
        return section_modulus(self.minor_axis_inertia, self.dimensions.flange_width / 2)

    @cached_property
    def major_axis_radius_of_gyration(self) -> Quantity:
        return _radius_of_gyration(moment_of_inertia=self.major_axis_inertia, gross_section_area=self.area)

    @cached_property
    def minor_axis_radius_of_gyration(self) -> Quantity:
        return _radius_of_gyration(moment_of_inertia=self.minor_axis_inertia, gross_section_area=self.area)

    @cached_property
    def warping_constant(self):
        return _warping_constant(
            moment_of_inertia=self.minor_axis_inertia,
            distance_between_flanges_centroid=self.dimensions.distance_between_centroids
        )

    @cached_property
    def torsional_constant(self) -> Quantity:
        return _doubly_symmetric_i_torsional_constant(
            flange_width=self.dimensions.flange_width,
            total_height=self.dimensions.total_height,
            flange_thickness=self.dimensions.flange_thickness,
            web_thickness=self.dimensions.web_thickness
        )

    @cached_property
    def torsional_radius_of_gyration(self):
        return _radius_of_gyration(
            moment_of_inertia=self.torsional_constant,
            gross_section_area=self.area
        )

    @cached_property
    def _major_axis_plastic_half_centroid(self) -> Quantity:
        return _areas_centroid(
            (
                (self._flange_area, self._flange_area_centroid_major_axis),
                (self.web_area / 2, self.dimensions.web_height / 4)
            )
        )

    @cached_property
    def _major_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self.web_area / 2

    @cached_property
    def major_axis_plastic_section_modulus(self):
        return 2 * self._major_axis_plastic_half_centroid * self._major_axis_plastic_half_area

    @cached_property
    def _minor_axis_plastic_half_centroid(self) -> Quantity:
        return _areas_centroid(
            (
                (self._flange_area, self.dimensions.flange_width / 4),
                (self.web_area / 2, self.dimensions.web_thickness / 4)
            )
        )

    @cached_property
    def _minor_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self.web_area / 2

    @cached_property
    def minor_axis_plastic_section_modulus(self):
        return 2 * self._minor_axis_plastic_half_area * self._minor_axis_plastic_half_centroid


@dataclass
class DoublySymmetricIDimensionsUserDefined(DoublySymmetricIDimensions):
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Quantity
    web_radii: Quantity = Quantity(0, "mm")

    @property
    def web_height(self):
        return _web_height(self.total_height, self.flange_thickness)

    @cached_property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness

    @cached_property
    def web_height_corrected(self):
        if self.web_radii:
            return self.web_height - self.web_radii
        else:
            return self.web_height


@dataclass
class DoublySymmetricIWebSlenderness(ElementSlenderness):
    profile: "DoublySymmetricI"

    @cached_property
    def axial_compression_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.49
        )

    @cached_property
    def ratio(self) -> float:
        return self.profile.dimensions.web_height_corrected / self.profile.dimensions.web_thickness

    @cached_property
    def axial_compression_value(self):
        limit = self.axial_compression_limit_ratio
        ratio = self.ratio
        if ratio < limit:
            return Slenderness.NON_SLENDER
        return Slenderness.SLENDER

    @cached_property
    def flexural_compact_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=3.76
        )

    @cached_property
    def flexural_slender_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=5.7
        )

    @cached_property
    def flexural_value(self):
        limit_slender = self.flexural_slender_limit_ratio
        limit_compact = self.flexural_compact_limit_ratio
        ratio = self.ratio
        return _flexural_slenderness_per_element(limit_slender=limit_slender, limit_compact=limit_compact, ratio=ratio)

    @cached_property
    def axial_compression(self):
        return AxialSlendernessImplementation(
            value=self.axial_compression_value,
            limit_ratio=self.axial_compression_limit_ratio,
        )

    @cached_property
    def flexural_minor_axis(self):
        return FlexuralSlendernessImplementation(
            value=self.flexural_value,
            slender_limit_ratio=self.flexural_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio
        )

    @cached_property
    def flexural_major_axis(self):
        return FlexuralSlendernessImplementation(
            value=self.flexural_value,
            slender_limit_ratio=self.flexural_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio
        )


@dataclass
class DoublySymmetricIFlangeSlenderness(ElementSlenderness):
    profile: "DoublySymmetricI"

    @cached_property
    def kc_coefficient(self):
        return _kc_coefficient(
            web_height=self.profile.dimensions.web_height_corrected,
            web_thickness=self.profile.dimensions.web_thickness
        )

    @cached_property
    def axial_limit_ratio_rolled(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.56,
        )

    @cached_property
    def axial_limit_ratio_built_up(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.64,
            kc_coefficient=self.kc_coefficient
        )

    @cached_property
    def axial_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.axial_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.axial_limit_ratio_built_up
        }
        return table[self.profile.construction]

    @cached_property
    def ratio(self) -> float:
        return self.profile.dimensions.flange_width / 2 / self.profile.dimensions.flange_thickness

    @cached_property
    def axial_compression_value(self):
        limit = self.axial_limit_ratio
        ratio = self.ratio
        if ratio < limit:
            return Slenderness.NON_SLENDER
        return Slenderness.SLENDER

    @cached_property
    def flexural_compact_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=0.38
        )

    @cached_property
    def flexural_slender_limit_ratio_rolled(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.0
        )

    @cached_property
    def flexural_slender_limit_ratio_built_up(self):
        stress = _limit_stress_built_up_sections(
            yield_stress=self.profile.material.yield_stress,
            section_modulus_tension=self.profile.area_properties.major_axis_elastic_section_modulus,
            section_modulus_compression=self.profile.area_properties.major_axis_elastic_section_modulus,
        )
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=stress,
            factor=0.95,
            kc_coefficient=self.kc_coefficient
        )

    @cached_property
    def flexural_major_axis_slender_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.flexural_slender_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.flexural_slender_limit_ratio_built_up
        }
        return table[self.profile.construction]

    @cached_property
    def flexural_minor_axis_slender_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1
        )

    @cached_property
    def flexural_minor_axis_value(self):
        limit_slender = self.flexural_minor_axis_slender_limit_ratio
        limit_compact = self.flexural_compact_limit_ratio
        ratio = self.ratio
        return _flexural_slenderness_per_element(limit_slender=limit_slender, limit_compact=limit_compact, ratio=ratio)

    @cached_property
    def flexural_major_axis_value(self):
        limit_slender = self.flexural_major_axis_slender_limit_ratio
        limit_compact = self.flexural_compact_limit_ratio
        ratio = self.ratio
        return _flexural_slenderness_per_element(limit_slender=limit_slender, limit_compact=limit_compact, ratio=ratio)

    @cached_property
    def axial_compression(self):
        return AxialSlendernessImplementation(
            value=self.axial_compression_value,
            limit_ratio=self.axial_limit_ratio,
        )

    @cached_property
    def flexural_minor_axis(self):
        return FlexuralSlendernessImplementation(
            value=self.flexural_minor_axis_value,
            slender_limit_ratio=self.flexural_minor_axis_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio
        )

    @cached_property
    def flexural_major_axis(self):
        return FlexuralSlendernessImplementation(
            value=self.flexural_major_axis_value,
            slender_limit_ratio=self.flexural_major_axis_slender_limit_ratio,
            compact_limit_ratio=self.flexural_compact_limit_ratio
        )


@dataclass
class ElementSlendernessDefaultImplementation(ElementSlenderness):
    axial_compression: AxialSlenderness
    flexural_minor_axis: FlexuralSlenderness
    flexural_major_axis: FlexuralSlenderness
    ratio: float


@dataclass
class DoublySymmetricI:
    dimensions: DoublySymmetricIDimensions
    material: Material
    area_properties: Optional["AreaPropertiesWithWeb"] = None
    construction: ConstructionType = ConstructionType.ROLLED
    coefficient_c: float = 1.0

    def __post_init__(self):
        if not self.area_properties:
            self.area_properties = DoublySymmetricIAreaPropertiesFromDimensions(self.dimensions)

    @cached_property
    def default_table(self):
        dimensions_table = self.dimensions.default_table
        area_properties_table = self.area_properties.data_table_df
        extra_table = extract_input_dataframe(
            obj=self,
            extraction_type=DoublySymmetricI,
            filter_names=["dimensions", "area_properties", "material"]
        )
        warping_constant_table = pd.DataFrame({"warping_constant": [self.warping_constant]})
        return pd.concat((dimensions_table, area_properties_table, warping_constant_table, extra_table), axis=1)

    @cached_property
    def web_shear_buckling_coefficient(self):
        return 5

    @cached_property
    def web_shear_coefficient_limit_0(self):
        return _web_shear_coefficient_limit(
            factor=2.24,
            web_shear_buckling_coefficient=1.,
            modulus_linear=self.material.modulus_linear,
            yield_stress=self.material.yield_stress
        )

    @cached_property
    def web_shear_coefficient_limit_i(self):
        return _web_shear_coefficient_limit(
            factor=1.1,
            web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
            modulus_linear=self.material.modulus_linear,
            yield_stress=self.material.yield_stress
        )

    @cached_property
    def web_shear_coefficient_limit_ii(self):
        return _web_shear_coefficient_limit(
            factor=1.37,
            web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
            modulus_linear=self.material.modulus_linear,
            yield_stress=self.material.yield_stress
        )

    @cached_property
    def web_shear_coefficient_iii(self):
        return _web_shear_coefficient_iii(
            shear_buckling_coefficient=self.web_shear_buckling_coefficient,
            modulus_linear=self.material.modulus_linear,
            yield_stress=self.material.yield_stress,
            web_slenderness=self.slenderness.web.ratio
        )

    @cached_property
    def web_shear_coefficient(self):
        if self.slenderness.web.ratio <= self.web_shear_coefficient_limit_0:
            return 1.0
        if self.slenderness.web.ratio < self.web_shear_coefficient_limit_i:
            return 1.0
        elif self.slenderness.web.ratio < self.web_shear_coefficient_limit_ii:
            return self.web_shear_coefficient_limit_i / self.slenderness.web.ratio
        else:
            return self.web_shear_coefficient_iii

    @cached_property
    def warping_constant(self):
        if self.area_properties.warping_constant:
            return self.area_properties.warping_constant
        return _warping_constant(
            moment_of_inertia=self.area_properties.minor_axis_inertia,
            distance_between_flanges_centroid=self.dimensions.distance_between_centroids
        )

    @cached_property
    def effective_radius_of_gyration(self):
        return _effective_radius_of_gyration(
            major_section_modulus=self.area_properties.major_axis_elastic_section_modulus,
            minor_inertia=self.area_properties.minor_axis_inertia,
            warping_constant=self.warping_constant,
        )

    @cached_property
    def limit_length_torsional_buckling(self):
        return _limiting_length_torsional_buckling(
            modulus=self.material.modulus_linear,
            yield_stress=self.material.yield_stress,
            section_modulus=self.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.area_properties.torsional_constant,
            effective_radius_of_gyration=self.effective_radius_of_gyration,
            distance_between_centroids=self.dimensions.distance_between_centroids,
            coefficient_c=self.coefficient_c,
        )

    @cached_property
    def limit_length_yield(self):
        return _limiting_length_yield(
            modulus=self.material.modulus_linear,
            radius_of_gyration=self.area_properties.minor_axis_radius_of_gyration,
            yield_stress=self.material.yield_stress
        )

    @cached_property
    def slenderness(self):
        return DoublySymmetricIFlangeWebSectionSlenderness(profile=self)

    def elastic_torsional_buckling_stress(self, beam: "BeamCompressionTorsionalBuckling"):
        return _elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.material.modulus_linear,
            modulus_shear=self.material.modulus_shear,
            effective_length_factor_torsional_buckling=beam.factor_k,
            member_length=beam.unbraced_length,
            torsional_constant=self.area_properties.torsional_constant,
            major_axis_inertia=self.area_properties.major_axis_inertia,
            minor_axis_inertia=self.area_properties.minor_axis_inertia,
            warping_constant=self.warping_constant
        )

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionTorsionalBuckling"):
        return _critical_compression_stress_buckling_default(
            member_slenderness=beam.torsional_slenderness,
            member_slenderness_limit=beam.member_slenderness_limit,
            yield_stress=self.material.yield_stress,
            elastic_buckling_stress=self.elastic_torsional_buckling_stress(beam),
        )

    @cached_property
    def latex(self):
        return DoublySymmetricIUserDefinedLatex(self)