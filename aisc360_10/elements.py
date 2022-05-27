from collections import namedtuple
from functools import cached_property
from typing import Protocol, Any, Collection, runtime_checkable, NamedTuple
from dataclasses import dataclass, field, is_dataclass, make_dataclass, asdict
import pandas as pd

from quantities import Quantity, UnitQuantity, cm, UnitQuantity, m, mm, GPa, MPa, N

from aisc360_10.criteria import (
    DesignStrength, SafetyFactorType, SafetyFactor, AllowableStrengthDesign,
    LoadAndResistanceFactorDesign
)
from aisc360_10.elements_latex import (
    MaterialLatex, AreaPropertiesLatex, DoublySymmetricIDimensionsLatex,
    DoublySymmetricISlendernessLatex, BeamCompressionEffectiveLengthLatex, BeamFlexureDoublySymmetricLatex,
    BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex, DoublySymmetricIUserDefinedLatex
)
from aisc360_10.helpers import (
    _areas_centroid, _critical_compression_stress_buckling_default,
    _doubly_symmetric_i_torsional_constant, _effective_radius_of_gyration, _elastic_flexural_buckling_stress,
    _elastic_torsional_buckling_stress_doubly_symmetric_member, _flexural_flange_local_buckling_non_compact,
    _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric,
    _flexural_lateral_torsional_buckling_strength,
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b,
    _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c,
    _flexural_major_axis_yield_strength,
    _flexural_minor_axis_yield_strength, _flexural_slenderness_per_element, _flexural_slenderness_several_elements,
    _flexure_and_axial_compression_h1_1_criteria, _kc_coefficient,
    _lateral_torsional_buckling_modification_factor_default, _limit_ratio_default, _limit_stress_built_up_sections,
    _limiting_length_torsional_buckling, _limiting_length_yield, _member_slenderness_ratio, _minimum_allowed_strength,
    _nominal_compressive_strength, _radius_of_gyration, _rectangle_area, _section_modulus, _self_inertia,
    _transfer_inertia, _warping_constant, ConstructionType, Slenderness, _member_slenderness_limit,
    _axial_strength_ratio
)
from aisc360_10.latex_helpers import (
    _slenderness_default_limit_ratio_latex, _member_slenderness_minor_axis_flexural_bucking_latex,
    _dataframe_table_columns, _elastic_buckling_critical_stress_latex,
    _axial_compression_non_slender_critical_stress_lower_than,
    _axial_compression_non_slender_critical_stress_greater_than, _axial_compression_nominal_strength,
    _process_quantity_entry_config, _design_strength_asd, _design_strength_lfrd, _design_strength,
    _flexural_yield_nominal_strength, _limit_length_yield, _limit_length_lateral_torsional_buckling,
    _flexural_lateral_torsional_buckling_strength_case_b, _build_doc, CONCATENATE_STRING,
    _effective_radius_of_gyration_equation, _flexure_compression_h1_criteria_equation, _axial_strength_ratio_equation,
    _ratio_equation
)
from aisc360_10.report_config import ReportConfig

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")

config_dict = ReportConfig()


@runtime_checkable
class DataClass(Protocol):
    def __dataclass_fields__(self):
        ...


def _extract_dataframe(obj: Any, extraction_type: Any, filter_names: list[str] = None):
    filter_names = filter_names or []
    dict_ = {key: [getattr(obj, key)] for key in extraction_type.__annotations__.keys() if key not in filter_names}
    return pd.DataFrame(dict_)


class TableKeys(Protocol):
    @classmethod
    def table_keys(cls):
        return cls.__annotations__.keys()


class Material(Protocol):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity

    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=Material, filter_names=filter_names)

    @cached_property
    def data_table_df(self):
        return self.table(filter_names=["poisson_ratio"])

    @cached_property
    def latex(self):
        return MaterialLatex(self)


@dataclass
class IsoTropicMaterial(Material):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity
    density: Quantity | None = None


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

    # Don't be mad future me. At least it worked
    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=AreaProperties, filter_names=filter_names)

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
class DoublySymmetricIUserDefinedFlangeWebSectionSlenderness(FlangeWebSectionSlenderness):
    profile: "DoublySymmetricIUserDefined"

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

    def torsional_buckling_critical_stress_effective_length(self, beam: "BeamCompressionEffectiveLength") -> Quantity:
        raise NotImplementedError


class DoublySymmetricIDimensions(Protocol):
    flange_width: Quantity
    flange_thickness: Quantity
    web_height: Quantity
    web_thickness: Quantity
    total_height: Quantity
    distance_between_centroids: Quantity

    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=DoublySymmetricIDimensions, filter_names=filter_names)

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
    def _web_area(self):
        return _rectangle_area(width=self.dimensions.web_thickness, height=self.dimensions.web_height)

    @cached_property
    def area(self) -> Quantity:
        return self._web_area + 2 * self._flange_area

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
        return _section_modulus(self.major_axis_inertia, self.dimensions.total_height / 2)

    @cached_property
    def minor_axis_elastic_section_modulus(self) -> Quantity:
        return _section_modulus(self.minor_axis_inertia, self.dimensions.flange_width / 2)

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
                (self._web_area / 2, self.dimensions.web_height / 4)
            )
        )

    @cached_property
    def _major_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self._web_area / 2

    @cached_property
    def major_axis_plastic_section_modulus(self):
        return 2 * self._major_axis_plastic_half_centroid * self._major_axis_plastic_half_area

    @cached_property
    def _minor_axis_plastic_half_centroid(self) -> Quantity:
        return _areas_centroid(
            (
                (self._flange_area, self.dimensions.flange_width / 4),
                (self._web_area / 2, self.dimensions.web_thickness / 4)
            )
        )

    @cached_property
    def _minor_axis_plastic_half_area(self) -> Quantity:
        return self._flange_area + self._web_area / 2

    @cached_property
    def minor_axis_plastic_section_modulus(self):
        return 2 * self._minor_axis_plastic_half_area * self._minor_axis_plastic_half_centroid


@dataclass
class DoublySymmetricIDimensionsUserDefined(DoublySymmetricIDimensions):
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Quantity
    web_height: Quantity | None = None

    def __post_init__(self):
        if not self.web_height:
            self.web_height = self.total_height - 2 * self.flange_thickness

    @cached_property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness


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
    profile: "DoublySymmetricIUserDefined"

    @cached_property
    def axial_compression_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.profile.material.modulus_linear,
            stress=self.profile.material.yield_stress,
            factor=1.49
        )

    @cached_property
    def ratio(self) -> float:
        return self.profile.dimensions.web_height / self.profile.dimensions.web_thickness

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
    profile: "DoublySymmetricIUserDefined"

    @cached_property
    def kc_coefficient(self):
        return _kc_coefficient(
            web_height=self.profile.dimensions.web_height,
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
class DoublySymmetricIUserDefined(SectionProfile):
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
        extra_table = _extract_dataframe(
            obj=self,
            extraction_type=DoublySymmetricIUserDefined,
            filter_names=["dimensions", "area_properties", "material"]
        )
        warping_constant_table = pd.DataFrame({"warping_constant": [self.warping_constant]})
        return pd.concat((dimensions_table, area_properties_table, warping_constant_table, extra_table), axis=1)

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
        return DoublySymmetricIUserDefinedFlangeWebSectionSlenderness(profile=self)

    def elastic_torsional_buckling_stress(self, beam: "BeamCompressionEffectiveLength"):
        return _elastic_torsional_buckling_stress_doubly_symmetric_member(
            modulus_linear=self.material.modulus_linear,
            modulus_shear=self.material.modulus_shear,
            effective_length_factor_torsional_buckling=beam.factor_k_torsion,
            member_length=beam.unbraced_length,
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


class BeamCompression(Protocol):
    strength_flexural_buckling: Quantity
    strength_torsional_buckling: Quantity


@dataclass
class BeamCompressionEffectiveLength(BeamCompression):
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    required_strength: Quantity | None = None
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def minor_axis_slenderness(self):
        return _member_slenderness_ratio(
            factor_k=self.factor_k_minor_axis,
            radius_of_gyration=self.profile.area_properties.minor_axis_radius_of_gyration,
            unbraced_length=self.unbraced_length
        )

    @cached_property
    def torsional_slenderness(self):
        return _member_slenderness_ratio(
            factor_k=self.factor_k_torsion,
            unbraced_length=self.unbraced_length,
            radius_of_gyration=self.profile.area_properties.torsional_radius_of_gyration
        )

    @cached_property
    def elastic_flexural_buckling_stress(self):
        return _elastic_flexural_buckling_stress(
            modulus_linear=self.profile.material.modulus_linear,
            member_slenderness_ratio=self.minor_axis_slenderness
        )

    @cached_property
    def member_slenderness_limit(self):
        return _member_slenderness_limit(
            modulus_linear=self.profile.material.modulus_linear,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def flexural_buckling_critical_stress(self):
        return _critical_compression_stress_buckling_default(
            member_slenderness=self.minor_axis_slenderness,
            elastic_buckling_stress=self.elastic_flexural_buckling_stress,
            member_slenderness_limit=self.member_slenderness_limit,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def torsional_buckling_critical_stress(self):
        return self.profile.torsional_buckling_critical_stress_effective_length(self)

    @cached_property
    def strength_flexural_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            self.flexural_buckling_critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def strength_torsional_buckling(self) -> Quantity:
        return _nominal_compressive_strength(
            critical_stress=self.torsional_buckling_critical_stress,
            sectional_area=self.profile.area_properties.area
        )

    @cached_property
    def nominal_strength(self):
        return self.strength_flexural_buckling

    @cached_property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @cached_property
    def strength_resume(self):
        return pd.DataFrame(
            {
                "strength flexural buckling": [self.safety_factor.allowable_value(self.nominal_strength)]
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
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity
    lateral_torsional_buckling_modification_factor: float = 1.
    required_major_axis_flexure_strength: Quantity | None = None
    required_minor_axis_flexure_strength: Quantity | None = None
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
            length_between_braces=self.unbraced_length,
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
            length_between_braces=self.unbraced_length,
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
            length_between_braces=self.unbraced_length,
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
            "strength yield": [self.safety_factor.allowable_value(self.strength_major_axis_yield)],
            "strength lateral torsion": [
                self.safety_factor.allowable_value(
                    self.strength_lateral_torsion
                )
            ]
        }
        if strength_local_buckling:
            df.update(
                {
                    "strength lateral torsion": [self.safety_factor.allowable_value(strength_local_buckling)]
                }
            )
        return pd.DataFrame(df)

    @cached_property
    def latex(self):
        return BeamFlexureDoublySymmetricLatex(self)


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLength:
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity
    required_axial_strength: Quantity | None = None
    required_major_axis_flexure_strength: Quantity | None = None
    required_minor_axis_flexure_strength: Quantity | None = None
    lateral_torsional_buckling_modification_factor: float = 1.0
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    def table(self, filter_names: list[str] = None):
        return _extract_dataframe(obj=self, extraction_type=self, filter_names=filter_names)

    @cached_property
    def data_table_df(self):
        return self.table(
            filter_names=[
                "profile",
                "safety_factor",
                "factor_k_torsion",
                "required_axial_strength",
                "required_major_axis_flexure_strength",
                "required_minor_axis_flexure_strength"

            ]
        )

    @cached_property
    def compression(self):
        return BeamCompressionEffectiveLength(
            profile=self.profile,
            unbraced_length=self.unbraced_length,
            factor_k_torsion=self.factor_k_torsion,
            factor_k_major_axis=self.factor_k_major_axis,
            factor_k_minor_axis=self.factor_k_minor_axis,
            required_strength=self.required_axial_strength
        )

    @cached_property
    def flexure(self):
        return BeamFlexureDoublySymmetric(
            profile=self.profile,
            unbraced_length=self.unbraced_length,
            required_major_axis_flexure_strength=self.required_major_axis_flexure_strength,
            required_minor_axis_flexure_strength=self.required_minor_axis_flexure_strength
        )

    @cached_property
    def compression_flexure_combined_criteria_h1_1(self) -> float:
        return _flexure_and_axial_compression_h1_1_criteria(
            available_axial_strength=self.compression.design_strength,
            required_axial_strength=self.required_axial_strength,
            available_major_axis_flexural_strength=self.flexure.design_strength_major_axis,
            required_major_axis_flexural_strength=self.required_major_axis_flexure_strength,
            available_minor_axis_flexural_strength=self.flexure.design_strength_minor_axis,
            required_minor_axis_flexural_strength=self.required_minor_axis_flexure_strength,
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
                "required_axial_strength": [self.required_axial_strength],
                "required_major_axis_flexure_strength": [self.required_major_axis_flexure_strength],
                "required_minor_axis_flexure_strength": [self.required_minor_axis_flexure_strength],
            }
        )

    @cached_property
    def results_h1_df(self):
        required_df = self.required_strengths_df
        return pd.concat(
            (required_df, pd.DataFrame({"h1_criteria": [self.compression_flexure_combined_criteria_h1_1]}),),
            axis=1,
        )
