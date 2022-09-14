from functools import cached_property, partial
from typing import Protocol
from dataclasses import dataclass
import pandas as pd

from quantities import Quantity, UnitQuantity, m, N

from structure_scripts.aisc_360_10.criteria import (
    SafetyFactor, AllowableStrengthDesign
)
from structure_scripts.aisc_360_10.elements_latex import (
    AreaPropertiesLatex, DoublySymmetricIDimensionsLatex,
    BeamCompressionEffectiveLengthLatex, BeamFlexureDoublySymmetricLatex,
    BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex, DoublySymmetricIUserDefinedLatex
)
from structure_scripts.aisc_360_10.helpers import (
    _areas_centroid, _critical_compression_stress_buckling_default,
    _doubly_symmetric_i_torsional_constant, _effective_radius_of_gyration, _elastic_flexural_buckling_stress,
    _elastic_torsional_buckling_stress_doubly_symmetric_member, _flexural_flange_local_buckling_non_compact,
    _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric,
    _flexural_lateral_torsional_buckling_strength,
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b,
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c,
    _flexural_major_axis_yield_strength,
    _flexural_minor_axis_yield_strength, _flexural_slenderness_per_element,
    _flexural_and_axial_compression_h1_1_criteria, _kc_coefficient,
    _lateral_torsional_buckling_modification_factor_default, _limit_ratio_default, _limit_stress_built_up_sections,
    _limiting_length_torsional_buckling, _limiting_length_yield, _minimum_allowed_strength,
    _nominal_compressive_strength, _radius_of_gyration, _rectangle_area, _self_inertia,
    _transfer_inertia, _warping_constant, ConstructionType, Slenderness, _member_slenderness_limit,
    _axial_strength_ratio, _web_shear_coefficient_limit, _nominal_shear_strength, _web_shear_coefficient_ii,
    _web_shear_coefficient_iii
)
from structure_scripts.shared.helpers import ratio_simplify, member_slenderness_ratio, section_modulus
from structure_scripts.shared.report_config import config_dict
from structure_scripts.shared.data import extract_input_dataframe
from structure_scripts.shared.materials import Material

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")




class AreaProperties(Protocol):
    area: Quantity
    major_axis_inertia: Quantity
    major_axis_elastic_section_modulus: Quantity
    major_axis_plastic_section_modulus: Quantity
    major_axis_radius_of_gyration: Quantity
    minor_axis_inertia: Quantity
    minor_axis_elastic_section_modulus: Quantity
    minor_axis_plastic_section_modulus: Quantity
    minor_axis_radius_of_gyration: Quantity
    torsional_constant: Quantity
    torsional_radius_of_gyration: Quantity
    warping_constant: Quantity
    web_area: Quantity

    # Don't be mad future me. At least it worked
    def table(self, filter_names: list[str] = None):
        return extract_input_dataframe(obj=self, extraction_type=AreaProperties, filter_names=filter_names)

    @cached_property
    def data_table_df(self):
        return self.table(filter_names=["torsional_radius_of_gyration", "warping_constant"])

    @cached_property
    def latex(self):
        return AreaPropertiesLatex(data=self)


class AxialSlenderness(Protocol):
    value: Slenderness
    limit_ratio: float
    ratio: float


@dataclass
class AxialSlendernessImplementation(AxialSlenderness):
    value: Slenderness
    limit_ratio: float


class FlexuralSlenderness(Protocol):
    value: Slenderness
    slender_limit_ratio: float
    compact_limit_ratio: float


@dataclass
class FlexuralSlendernessImplementation(FlexuralSlenderness):
    value: Slenderness
    slender_limit_ratio: float
    compact_limit_ratio: float


class ElementSlenderness(Protocol):
    axial_compression: AxialSlenderness
    flexural_minor_axis: FlexuralSlenderness
    flexural_major_axis: FlexuralSlenderness
    ratio: float


@dataclass
class ElementSlendernessDefaultImplementation(ElementSlenderness):
    axial_compression: AxialSlenderness
    flexural_minor_axis: FlexuralSlenderness
    flexural_major_axis: FlexuralSlenderness
    ratio: float


class FlangeWebSectionSlenderness(Protocol):
    flange: ElementSlenderness
    web: ElementSlenderness


@dataclass
class DoublySymmetricIFlangeWebSectionSlenderness(FlangeWebSectionSlenderness):
    profile: "DoublySymmetricI"

    @cached_property
    def flange(self):
        return DoublySymmetricIFlangeSlenderness(profile=self.profile)

    @cached_property
    def web(self):
        return DoublySymmetricIWebSlenderness(profile=self.profile)


class SectionProfile(Protocol):
    area_properties: AreaProperties
    material: Material
    coefficient_c: float
    effective_radius_of_gyration: Quantity
    warping_constant: Quantity
    web_shear_coefficient: float
    web_shear_buckling_coefficient: float

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionEffectiveLength") -> Quantity:
        raise NotImplementedError


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
class DoublySymmetricIAreaPropertiesFromDimensions(AreaProperties):
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
    web_radii: Quantity= Quantity(0, "mm")

    @property
    def web_height(self):
        return self.total_height - 2 * self.flange_thickness

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
class GenericAreaProperties(AreaProperties):
    area: Quantity
    major_axis_inertia: Quantity
    major_axis_elastic_section_modulus: Quantity
    minor_axis_inertia: Quantity
    minor_axis_elastic_section_modulus: Quantity
    torsional_constant: Quantity
    warping_constant: Quantity | None = None
    major_axis_plastic_section_modulus: Quantity | None = None
    minor_axis_plastic_section_modulus: Quantity | None = None
    major_axis_radius_of_gyration: Quantity | None = None
    minor_axis_radius_of_gyration: Quantity | None = None
    torsional_radius_of_gyration: Quantity | None = None

    def __post_init__(self):
        if not self.major_axis_plastic_section_modulus:
            self.major_axis_plastic_section_modulus = self.major_axis_elastic_section_modulus
        if not self.minor_axis_plastic_section_modulus:
            self.minor_axis_plastic_section_modulus = self.minor_axis_elastic_section_modulus
        if not self.minor_axis_radius_of_gyration:
            self.minor_axis_radius_of_gyration = _radius_of_gyration(self.minor_axis_inertia, self.area)
        if not self.major_axis_radius_of_gyration:
            self.major_axis_radius_of_gyration = _radius_of_gyration(self.major_axis_inertia, self.area)
        if not self.torsional_radius_of_gyration:
            self.torsional_radius_of_gyration = _radius_of_gyration(self.torsional_constant, self.area)


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
class DoublySymmetricI(SectionProfile):
    dimensions: DoublySymmetricIDimensions
    material: Material
    area_properties: AreaProperties | None = None
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
    def web_shear_coefficient(self):
        if self.slenderness.web.ratio < self.web_shear_coefficient_limit_i:
            return 1.0
        elif self.slenderness.web.ratio < self.web_shear_coefficient_limit_ii:
            return

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

    def elastic_torsional_buckling_stress(self, beam: "BeamCompressionEffectiveLength"):
        return _elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.material.modulus_linear,
            modulus_shear=self.material.modulus_shear,
            effective_length_factor_torsional_buckling=beam.factor_k_torsion,
            member_length=beam.unbraced_length_torsion,
            torsional_constant=self.area_properties.torsional_constant,
            major_axis_inertia=self.area_properties.major_axis_inertia,
            minor_axis_inertia=self.area_properties.minor_axis_inertia,
            warping_constant=self.warping_constant
        )

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionEffectiveLength"):
        return _critical_compression_stress_buckling_default(
            member_slenderness=beam.torsional_slenderness,
            member_slenderness_limit=beam.member_slenderness_limit,
            yield_stress=self.material.yield_stress,
            elastic_buckling_stress=self.elastic_torsional_buckling_stress(beam),
        )

    @cached_property
    def latex(self):
        return DoublySymmetricIUserDefinedLatex(self)


@dataclass
class BeamShearWeb:
    profile: DoublySymmetricI
    required_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def nominal_strength(self):
        return _nominal_shear_strength(
            yield_stress=self.profile.material.yield_stress,
            web_area=self.profile.area_properties.web_area,
            web_shear_coefficient=1,
        )

    @cached_property
    def web_shear_buckling_coefficient(self):
        return 5

    @cached_property
    def slenderness_limit(self):
        limit_function = partial(
            _web_shear_coefficient_limit,
            web_shear_buckling_coefficient=self.web_shear_buckling_coefficient,
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )
        return tuple(
            (
                limit_function(factor=factor)
                for factor in (1.1, 1.37)
            )
        )

    @cached_property
    def web_shear_coefficient(self):
        i, ii = self.slenderness_limit
        if self.profile.slenderness.web.ratio < i:
            coef = 1.
        elif self.profile.slenderness.web.ratio < ii:
            coef = _web_shear_coefficient_ii(
                shear_buckling_coefficient=self.web_shear_buckling_coefficient,
                modulus_linear=self.profile.material.modulus_linear,
                yield_stress=self.profile.material.yield_stress,
                web_slenderness=self.profile.slenderness.web.ratio
            )
        else:
            coef = _web_shear_coefficient_iii(
                shear_buckling_coefficient=self.web_shear_buckling_coefficient,
                modulus_linear=self.profile.material.modulus_linear,
                yield_stress=self.profile.material.yield_stress,
                web_slenderness=self.profile.slenderness.web.ratio
            )
        return coef

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength shear": [self.design_strength.rescale(kN)]
            }
        )

    @cached_property
    def criteria_df(self):
        return pd.DataFrame(
            {
                "shear_stress_criteria": [ratio_simplify(self.required_strength, self.design_strength)]
            }
        )


@dataclass
class BeamTorsionEffectiveLength:
    profile: DoublySymmetricI
    unbraced_length: Quantity
    factor_k: float = 1.0
    required_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k,
            unbraced_length=self.unbraced_length,
            radius_of_gyration=self.profile.area_properties.torsional_radius_of_gyration
        )

    @cached_property
    def member_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def critical_stress(self):
        return self.profile.torsional_buckling_critical_stress_effective_length(self)

    @cached_property
    def nominal_strength(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength torsion": [self.design_strength.rescale(kN)]
            }
        )


@dataclass
class BeamCompressionEffectiveLength:
    profile: DoublySymmetricI
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    unbraced_length_torsion: Quantity | None = None
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    required_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis
        if not self.unbraced_length_torsion:
            self.unbraced_length_torsion = self.unbraced_length_major_axis

    @cached_property
    def minor_axis_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k_minor_axis,
            radius_of_gyration=self.profile.area_properties.minor_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length_minor_axis
        )

    @cached_property
    def major_axis_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k_major_axis,
            radius_of_gyration=self.profile.area_properties.major_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length_major_axis
        )

    @cached_property
    def torsional_slenderness(self):
        return member_slenderness_ratio(
            factor_k=self.factor_k_major_axis,
            radius_of_gyration=self.profile.area_properties.major_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length_major_axis
        )

    @cached_property
    def elastic_flexural_buckling_stress_minor_axis(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.minor_axis_slenderness
        )

    @cached_property
    def elastic_flexural_buckling_stress_major_axis(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.major_axis_slenderness
        )

    # @cached_property
    # def elastic_flexural_buckling_stress_torsion(self):
    #     return _elastic_flexural_buckling_stress(
    #         modulus_linear=self.profile.material.modulus_linear,
    #         member_slenderness_ratio=self.torsional_slenderness
    #     )

    @cached_property
    def torsional_critical_stress(self):
        return self.profile.torsional_buckling_critical_stress_effective_length(self)

    @cached_property
    def member_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def flexural_buckling_critical_stress_minor_axis(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.minor_axis_slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress_minor_axis,
            member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def flexural_buckling_critical_stress_major_axis(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.major_axis_slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress_major_axis,
            member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def critical_stress_flexural_buckling(self) -> Quantity:
        return min(self.flexural_buckling_critical_stress_minor_axis, self.flexural_buckling_critical_stress_major_axis)

    @cached_property
    def strength_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.critical_stress_flexural_buckling,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_minor_axis_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress_minor_axis,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_major_axis_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress_major_axis,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_torsional_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.torsional_critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def design_strength_torsional_buckling(self):
        return self.safety_factor.allowable_value(self.strength_torsional_buckling)

    @cached_property
    def nominal_strength(self):
        return min(self.strength_flexural_buckling, self.strength_torsional_buckling)

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def design_strength_minor_axis(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength flexural buckling minor axis": [self.design_strength.rescale(kN)],
                "strength torsional buckling": [self.design_strength_torsional_buckling.rescale(kN)]
            }
        )

    @cached_property
    def latex(self):
        return BeamCompressionEffectiveLengthLatex(self)

    @cached_property
    def axial_strength_ratio(self):
        if not self.required_strength:
            return 0
        return _axial_strength_ratio(
            required_axial_strength=self.required_strength,
            available_axial_strength=self.design_strength
        )


class BeamFlexure(Protocol):
    strength_yielding: Quantity
    strength_lateral_torsional_buckling: Quantity | None
    strength_compression_local_buckling: Quantity | None


@dataclass
class LateralTorsionalBucklingModificationFactorDefault:
    moment_max: Quantity
    moment_quarter: Quantity
    moment_center: Quantity
    moment_three_quarter: Quantity

    @cached_property
    def value(self):
        return _lateral_torsional_buckling_modification_factor_default(
            self.moment_max,
            self.moment_quarter,
            self.moment_center,
            self.moment_three_quarter
        )


def lateral_torsional_buckling_modification_factor_default(
        moment_max: Quantity,
        moment_quarter: Quantity,
        moment_center: Quantity,
        moment_three_quarter: Quantity
):
    return _lateral_torsional_buckling_modification_factor_default(
        moment_max,
        moment_quarter,
        moment_center,
        moment_three_quarter
    )


@dataclass
class BeamFlexureDoublySymmetric:
    profile: DoublySymmetricI
    unbraced_length_major_axis: Quantity
    lateral_torsional_buckling_modification_factor: float = 1.
    required_major_axis_flexural_strength: Quantity | None = None
    required_minor_axis_flexural_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def plastic_moment_major_axis(self) -> Quantity:
        return self.strength_major_axis_yield

    @cached_property
    def strength_major_axis_yield(self) -> Quantity:
        return _flexural_major_axis_yield_strength(
            self.profile.material.yield_stress,
            self.profile.area_properties.major_axis_plastic_section_modulus
        )

    @cached_property
    def strength_lateral_torsion_compact_case_b(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.unbraced_length_major_axis,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
            limiting_length_yield=self.profile.limit_length_yield,
            mod_factor=self.lateral_torsional_buckling_modification_factor,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def critical_stress_lateral_torsional_buckling(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=self.lateral_torsional_buckling_modification_factor,
            length_between_braces=self.unbraced_length_major_axis,
            modulus=self.profile.material.modulus_linear,
            coefficient_c=self.profile.coefficient_c,
            distance_between_flange_centroids=self.profile.dimensions.distance_between_centroids,
            effective_radius_of_gyration=self.profile.effective_radius_of_gyration,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.profile.area_properties.torsional_constant
        )

    @cached_property
    def strength_lateral_torsion_compact_case_c(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            critical_stress=self.critical_stress_lateral_torsional_buckling,
        )

    @cached_property
    def strength_lateral_torsion(self) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength(
            case_b=self.strength_lateral_torsion_compact_case_b,
            case_c=self.strength_lateral_torsion_compact_case_c,
            length_between_braces=self.unbraced_length_major_axis,
            limiting_length_yield=self.profile.limit_length_yield,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
        )

    @cached_property
    def strength_major_axis_flange_local_buckling_slender(self):
        raise NotImplementedError

    @cached_property
    def strength_major_axis_flange_local_buckling_non_compact(self) -> Quantity:
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange.flexural_major_axis.compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange.flexural_major_axis.slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange.ratio,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def strength_minor_axis_flange_local_buckling_non_compact(self) -> Quantity:
        return _flexural_flange_local_buckling_non_compact(
            compact_limit_ratio=self.profile.slenderness.flange.flexural_minor_axis.compact_limit_ratio,
            slender_limit_ratio=self.profile.slenderness.flange.flexural_minor_axis.slender_limit_ratio,
            flange_ratio=self.profile.slenderness.flange.ratio,
            plastic_moment=self.plastic_moment_minor_axis,
            section_modulus=self.profile.area_properties.minor_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    def strength_minor_axis_flange_local_buckling_slender(self):
        raise NotImplementedError

    @cached_property
    def strength_minor_axis_yield(self) -> Quantity:
        return _flexural_minor_axis_yield_strength(
            yield_stress=self.profile.material.yield_stress,
            elastic_section_modulus=self.profile.area_properties.minor_axis_elastic_section_modulus,
            plastic_section_modulus=self.profile.area_properties.minor_axis_plastic_section_modulus
        )

    @cached_property
    def plastic_moment_minor_axis(self) -> Quantity:
        return self.strength_minor_axis_yield

    @cached_property
    def strength_major_axis_flange_local_buckling(self) -> Quantity:
        # TODO Implement slender flange local buckling strength
        table = {
            Slenderness.COMPACT: None,
            Slenderness.NON_COMPACT: self.strength_major_axis_flange_local_buckling_non_compact,
            # Slenderness.SLENDER: self.strength_major_axis_flange_local_buckling_slender,
        }
        return table[self.profile.slenderness.flange.flexural_major_axis.value]

    @cached_property
    def strength_minor_axis_flange_local_buckling(self) -> Quantity:
        table = {
            Slenderness.COMPACT: None,
            Slenderness.NON_COMPACT: self.strength_minor_axis_flange_local_buckling_non_compact,
            Slenderness.SLENDER: self.strength_minor_axis_flange_local_buckling_slender,
        }
        return table[self.profile.slenderness.flange.flexural_major_axis.value]

    @cached_property
    def nominal_strength_major_axis(self) -> Quantity:
        yield_ = self.strength_major_axis_yield
        lateral_torsional_buckling = self.strength_lateral_torsion
        flange_local_buckling = self.strength_major_axis_flange_local_buckling
        strengths = (yield_, lateral_torsional_buckling, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    @cached_property
    def nominal_strength_minor_axis(self) -> Quantity:
        yield_ = self.strength_minor_axis_yield
        flange_local_buckling = self.strength_minor_axis_flange_local_buckling
        strengths = (yield_, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    @cached_property
    def design_strength_major_axis(self) -> Quantity:
        return self.safety_factor.allowable_value(self.nominal_strength_major_axis)

    @cached_property
    def design_strength_minor_axis(self) -> Quantity:
        return self.safety_factor.allowable_value(self.nominal_strength_minor_axis)

    @cached_property
    def strength_resume(self) -> pd.DataFrame:
        strength_local_buckling = self.strength_major_axis_flange_local_buckling
        df = {
            "strength yield": [self.safety_factor.allowable_value(self.strength_major_axis_yield).rescale(kN * m)],
        }
        if self.strength_lateral_torsion:
            df.update(
                {
                    "strength lateral torsion": [
                        self.safety_factor.allowable_value(
                            self.strength_lateral_torsion
                        ).rescale(kN * m)
                    ]
                }
            )
        if self.strength_major_axis_flange_local_buckling:
            df.update(
                {
                    "strength local buckling": [
                        self.safety_factor.allowable_value(strength_local_buckling).rescale(kN * m)
                    ]
                }
            )
        return pd.DataFrame(df)

    @cached_property
    def latex(self):
        return BeamFlexureDoublySymmetricLatex(self)


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLength:
    profile: DoublySymmetricI
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    lateral_torsional_buckling_modification_factor: float = 1.0
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()
    required_axial_strength: Quantity = 0 * N
    required_major_axis_flexural_strength: Quantity = 0 * N * m
    required_minor_axis_flexural_strength: Quantity = 0 * N * m

    def table(self, filter_names: list[str] = None):
        return extract_input_dataframe(obj=self, extraction_type=self, filter_names=filter_names)

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis

    @cached_property
    def data_table_df(self):
        return self.table(
            filter_names=[
                "profile",
                "safety_factor",
                "required_axial_strength",
                "required_major_axis_flexural_strength",
                "required_minor_axis_flexural_strength"

            ]
        )

    @cached_property
    def compression(self):
        return BeamCompressionEffectiveLength(
            profile=self.profile,
            unbraced_length_major_axis=self.unbraced_length_major_axis,
            unbraced_length_minor_axis=self.unbraced_length_minor_axis,
            factor_k_major_axis=self.factor_k_major_axis,
            factor_k_minor_axis=self.factor_k_minor_axis,
            required_strength=self.required_axial_strength
        )

    @cached_property
    def flexure(self):
        return BeamFlexureDoublySymmetric(
            profile=self.profile,
            unbraced_length_major_axis=self.unbraced_length_major_axis,
            required_major_axis_flexural_strength=self.required_major_axis_flexural_strength,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexural_strength
        )

    @cached_property
    def compression_flexure_combined_criteria_h1_1(self) -> float:
        return _flexural_and_axial_compression_h1_1_criteria(
            available_axial_strength=self.compression.design_strength,
            required_axial_strength=self.required_axial_strength,
            available_major_axis_flexural_strength=self.flexure.design_strength_major_axis,
            required_major_axis_flexural_strength=self.required_major_axis_flexural_strength,
            available_minor_axis_flexural_strength=self.flexure.design_strength_minor_axis,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexural_strength,
        )

    @cached_property
    def resume(self):
        return pd.concat((self.compression.strength_resume, self.flexure.strength_resume), axis=1)

    @cached_property
    def latex(self):
        return BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex(self)

    @cached_property
    def required_strengths_df(self):
        return pd.DataFrame(
            {
                "required_axial_strength": [self.required_axial_strength.magnitude],
                "required_major_axis_flexure_strength": [self.required_major_axis_flexural_strength.magnitude],
                "required_minor_axis_flexure_strength": [self.required_minor_axis_flexural_strength.magnitude],
            }
        )

    @cached_property
    def criteria_df(self):
        return pd.DataFrame({"h1_criteria": [abs(self.compression_flexure_combined_criteria_h1_1)]})

    @cached_property
    def results_h1_df(self):
        required_df = self.required_strengths_df
        return pd.concat(
            (required_df, self.criteria_df,),
            axis=1,
        )


@dataclass
class Beam:
    profile: DoublySymmetricI
    unbraced_length_major_axis: Quantity
    unbraced_length_minor_axis: Quantity | None = None
    unbraced_length_torsion: Quantity | None = None
    lateral_torsional_buckling_modification_factor: float = 1.0
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()
    required_axial_strength: Quantity = 0 * N
    required_major_axis_flexural_strength: Quantity = 0 * N * m
    required_minor_axis_flexural_strength: Quantity = 0 * N * m
    required_shear_strength: Quantity = 0 * N
    required_torsional_strength: Quantity = 0 * N * m

    def __post_init__(self):
        if not self.unbraced_length_minor_axis:
            self.unbraced_length_minor_axis = self.unbraced_length_major_axis
        if not self.unbraced_length_torsion:
            self.unbraced_length_torsion = self.unbraced_length_major_axis

    @cached_property
    def compression_flexure_analysis(self):
        return BeamCompressionFlexureDoublySymmetricEffectiveLength(
            profile=self.profile,
            unbraced_length_minor_axis=self.unbraced_length_minor_axis,
            unbraced_length_major_axis=self.unbraced_length_major_axis,
            lateral_torsional_buckling_modification_factor=self.lateral_torsional_buckling_modification_factor,
            factor_k_major_axis=self.factor_k_major_axis,
            factor_k_minor_axis=self.factor_k_minor_axis,
            safety_factor=self.safety_factor,
            required_axial_strength=self.required_axial_strength,
            required_major_axis_flexural_strength=self.required_major_axis_flexural_strength,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexural_strength
        )

    @cached_property
    def compression_analysis(self):
        return self.compression_flexure_analysis.compression

    @cached_property
    def flexure_analysis(self):
        return self.compression_flexure_analysis.flexure

    @cached_property
    def shear_analysis(self):
        return BeamShearWeb(
            profile=self.profile,
            required_strength=self.required_shear_strength,
            safety_factor=self.safety_factor
        )

    @cached_property
    def torsion_analysis(self):
        return BeamTorsionEffectiveLength(
            profile=self.profile,
            unbraced_length=self.unbraced_length_torsion,
            factor_k=self.factor_k_torsion,
            required_strength=self.required_torsional_strength,
            safety_factor=self.safety_factor
        )

    @cached_property
    def critical_strengths(self):
        df = pd.concat(
            (
                self.compression_flexure_analysis.compression.strength_resume,
                self.compression_flexure_analysis.flexure.strength_resume,
                self.shear_analysis.strength_resume,
            ),
            axis=1
        )
        return df

    @cached_property
    def required_strengths_df(self):
        return pd.DataFrame(
            {
                "axial load": [self.required_axial_strength.rescale(config_dict.required_axial_strength.print_units)],
                "major axis load": [self.required_major_axis_flexural_strength.rescale(
                    config_dict.required_major_axis_flexural_strength.print_units)],
                "minor axis load": [self.required_minor_axis_flexural_strength.rescale(
                    config_dict.required_major_axis_flexural_strength.print_units)],
                "shear load": [self.required_shear_strength.rescale(config_dict.required_axial_strength.print_units)],
                "torsion load": [self.required_torsional_strength.rescale(
                    config_dict.required_major_axis_flexural_strength.print_units)]
            }
        )

    @cached_property
    def results(self):
        return pd.concat(
            (
                self.required_strengths_df,
                self.compression_flexure_analysis.criteria_df,
                self.shear_analysis.criteria_df
            ),
            axis=1
        )
