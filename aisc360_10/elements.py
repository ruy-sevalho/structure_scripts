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
    _effective_radius_of_gyration_equation, _flexure_compression_h1_criteria_equation
)
from aisc360_10.report_config import ReportConfig

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")


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
    def data_table_latex(self):
        return _dataframe_table_columns(
            df=self.data_table_df,
            unit_display="cell",
            include_description=True
        ).dumps()

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


def latex_wrapper_class(class_: DataClass, filtered_names: Collection[str] = None):
    filtered_names = filtered_names or []
    name = f"{class_.__name__}Latex"
    return make_dataclass(name, class_.__dataclass_fields__.keys())


IsoTropicMaterialLatex = latex_wrapper_class(IsoTropicMaterial)


def latex_wrapper(obj_: DataClass, filtered_names: Collection[str] = None, config_dict: ReportConfig = ReportConfig()):
    filtered_names = filtered_names or []
    attributes = {
        name: _process_quantity_entry_config(
            entry=getattr(obj_, name),
            print_config=getattr(config_dict, name)
        )
        for name in obj_.__dataclass_fields__
        if name not in filtered_names
    }
    # Latex = namedtuple("Latex", attributes.keys())
    Latex = make_dataclass("Latex", attributes.keys())
    return Latex(**attributes)


@dataclass
class MaterialLatex:
    material: Material
    report_config: ReportConfig = ReportConfig()

    @cached_property
    def modulus_linear(self):
        return _process_quantity_entry_config(
            entry=self.material.modulus_linear,
            print_config=self.report_config.modulus_linear
        )

    @cached_property
    def modulus_shear(self):
        return _process_quantity_entry_config(
            entry=self.material.modulus_shear,
            print_config=self.report_config.modulus_shear
        )

    @cached_property
    def yield_stress(self):
        return _process_quantity_entry_config(
            entry=self.material.yield_stress,
            print_config=self.report_config.yield_stress
        )


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
        return self.table(filter_names=["warping_constant", "torsional_radius_of_gyration"])

    @cached_property
    def data_table_latex(self):
        return _dataframe_table_columns(
            df=self.data_table_df,
            unit_display="cell",
            include_description=True
        ).dumps()

    @cached_property
    def latex(self):
        return AreaPropertiesLatex(data=self)


@dataclass
class AreaPropertiesLatex:
    data: AreaProperties
    report_config: ReportConfig = ReportConfig()

    @cached_property
    def area(self):
        return _process_quantity_entry_config(
            entry=self.data.area,
            print_config=self.report_config.area
        )

    @cached_property
    def major_axis_inertia(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_inertia,
            print_config=self.report_config.major_axis_inertia
        )

    @cached_property
    def major_axis_elastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_elastic_section_modulus,
            print_config=self.report_config.major_axis_elastic_section_modulus
        )

    @cached_property
    def major_axis_plastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_plastic_section_modulus,
            print_config=self.report_config.major_axis_plastic_section_modulus
        )

    @cached_property
    def major_axis_radius_of_gyration(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_radius_of_gyration,
            print_config=self.report_config.major_axis_radius_of_gyration
        )

    @cached_property
    def minor_axis_inertia(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_inertia,
            print_config=self.report_config.minor_axis_inertia
        )

    @cached_property
    def minor_axis_elastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_elastic_section_modulus,
            print_config=self.report_config.minor_axis_elastic_section_modulus
        )

    @cached_property
    def minor_axis_plastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_plastic_section_modulus,
            print_config=self.report_config.minor_axis_plastic_section_modulus
        )

    @cached_property
    def minor_axis_radius_of_gyration(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_radius_of_gyration,
            print_config=self.report_config.minor_axis_radius_of_gyration
        )

    @cached_property
    def torsional_constant(self):
        return _process_quantity_entry_config(
            entry=self.data.torsional_constant,
            print_config=self.report_config.torsional_constant
        )

    @cached_property
    def torsional_constant(self):
        return _process_quantity_entry_config(
            entry=self.data.torsional_constant,
            print_config=self.report_config.torsional_constant
        )

    @cached_property
    def warping_constant(self):
        return _process_quantity_entry_config(
            entry=self.data.warping_constant,
            print_config=self.report_config.warping_constant
        )


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
class FlangeWebSectionSlendernessDefaultImplementation(FlangeWebSectionSlenderness):
    flange: "DoublySymmetricIFlangeSlenderness"
    web: "DoublySymmetricIWebSlenderness"


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
class DoublySymmetricIDimensionsLatex:
    model: DoublySymmetricIDimensions
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def distance_between_centroids(self):
        return _process_quantity_entry_config(
            entry=self.model.distance_between_centroids,
            print_config=self.config_dict.distance_between_centroids
        )


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
    area_properties: AreaProperties
    dimensions: DoublySymmetricIDimensions
    construction: ConstructionType
    material: Material

    @cached_property
    def axial_compression_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=1.49
        )

    @cached_property
    def ratio(self) -> float:
        return self.dimensions.web_height / self.dimensions.web_thickness

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
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=3.76
        )

    @cached_property
    def flexural_slender_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
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
    area_properties: AreaProperties
    dimensions: DoublySymmetricIDimensions
    construction: ConstructionType
    material: Material

    @cached_property
    def kc_coefficient(self):
        return _kc_coefficient(web_height=self.dimensions.web_height, web_thickness=self.dimensions.web_thickness)

    @cached_property
    def axial_limit_ratio_rolled(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=0.56,
        )

    @cached_property
    def axial_limit_ratio_built_up(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=0.64,
            kc_coefficient=self.kc_coefficient
        )

    @cached_property
    def axial_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.axial_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.axial_limit_ratio_built_up
        }
        return table[self.construction]

    @cached_property
    def ratio(self):
        return self.dimensions.flange_width / 2 / self.dimensions.flange_thickness

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
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=0.38
        )

    @cached_property
    def flexural_slender_limit_ratio_rolled(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
            factor=1.0
        )

    @cached_property
    def flexural_slender_limit_ratio_built_up(self):
        stress = _limit_stress_built_up_sections(
            yield_stress=self.material.yield_stress,
            section_modulus_tension=self.area_properties.major_axis_elastic_section_modulus,
            section_modulus_compression=self.area_properties.major_axis_elastic_section_modulus,
        )
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
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
        return table[self.construction]

    @cached_property
    def flexural_minor_axis_slender_limit_ratio(self):
        return _limit_ratio_default(
            modulus_linear=self.material.modulus_linear,
            stress=self.material.yield_stress,
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
class DoublySymmetricIFlangeAxialCompressionSlendernessLatex:
    model: "DoublySymmetricIFlangeSlenderness"
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def axial_limit_ratio_rolled(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.axial_limit_ratio_rolled),
            print_config=self.config_dict.slender_limit_ratio
        )

    @cached_property
    def slender_limit_ratio_rolled(self):
        return _slenderness_default_limit_ratio_latex(
            factor="0.56",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.axial_limit_ratio_rolled,
            limit_ratio_type="slender"
        )

    @cached_property
    def slender_limit_ratio_built_up(self):
        return "Not Implemented"

    @cached_property
    def limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.slender_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.slender_limit_ratio_built_up
        }
        return table[self.model.construction]


@dataclass
class DoublySymmetricIFlangeFlexuralMajorAxisSlendernessLatex:
    model: "DoublySymmetricIFlangeSlenderness"
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def flexural_slender_limit_ratio_rolled(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_slender_limit_ratio_rolled),
            print_config=self.config_dict.slender_limit_ratio
        )

    @cached_property
    def slender_limit_ratio_rolled(self):
        return _slenderness_default_limit_ratio_latex(
            factor="1.0",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.flexural_slender_limit_ratio_rolled,
            limit_ratio_type="slender"
        )

    @cached_property
    def flexural_major_axis_compact_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_major_axis.compact_limit_ratio),
            print_config=self.config_dict.compact_limit_ratio
        )

    @cached_property
    def compact_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="0.38",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.flexural_major_axis_compact_limit_ratio,
            limit_ratio_type="compact"
        )

    @cached_property
    def slender_limit_ratio_built_up(self):
        return "Not Implemented"

    @cached_property
    def slender_limit_ratio(self):
        table = {
            ConstructionType.ROLLED: self.slender_limit_ratio_rolled,
            ConstructionType.BUILT_UP: self.slender_limit_ratio_built_up
        }
        return table[self.model.construction]

    @cached_property
    def limit_ratio(self):
        return f"{self.slender_limit_ratio} \n {self.compact_limit_ratio}"


@dataclass
class DoublySymmetricIFlangeFlexuralMinorAxisSlendernessLatex:
    model: "DoublySymmetricIFlangeSlenderness"
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def flexural_minor_axis_slender_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_minor_axis.slender_limit_ratio),
            print_config=self.config_dict.slender_limit_ratio
        )

    @cached_property
    def flexural_minor_axis_compact_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_minor_axis.compact_limit_ratio),
            print_config=self.config_dict.compact_limit_ratio
        )

    @cached_property
    def slender_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="1.0",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.flexural_minor_axis_slender_limit_ratio,
            limit_ratio_type="slender"
        )

    @cached_property
    def compact_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="0.38",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.flexural_minor_axis_compact_limit_ratio,
            limit_ratio_type="compact"
        )

    @cached_property
    def limit_ratio(self):
        return f"{self.slender_limit_ratio} \n {self.compact_limit_ratio}"


@dataclass
class DoublySymmetricIWebAxialCompressionSlendernessLatex:
    model: "DoublySymmetricIWebSlenderness"
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def axial_compression_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.axial_compression.limit_ratio),
            print_config=self.config_dict.compact_limit_ratio
        )

    @cached_property
    def limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="1.49",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.axial_compression_limit_ratio,
            limit_ratio_type="slender"
        )


@dataclass
class DoublySymmetricIWebFlexuralSlendernessLatex:
    model: "DoublySymmetricIWebSlenderness"
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def flexural_slender_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_slender_limit_ratio),
            print_config=self.config_dict.slender_limit_ratio
        )

    @cached_property
    def flexural_compact_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_compact_limit_ratio),
            print_config=self.config_dict.compact_limit_ratio
        )

    @cached_property
    def slender_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="3.76",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.flexural_slender_limit_ratio,
            limit_ratio_type="slender"
        )

    @cached_property
    def compact_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="5.70",
            modulus=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_ratio=self.flexural_compact_limit_ratio,
            limit_ratio_type="compact"
        )

    @cached_property
    def limit_ratio(self):
        return f"{self.slender_limit_ratio} \n {self.compact_limit_ratio}"


@dataclass
class DoublySymmetricIAxialCompressionSlendernessLatex:
    flange: DoublySymmetricIFlangeAxialCompressionSlendernessLatex
    web: DoublySymmetricIWebAxialCompressionSlendernessLatex

    @cached_property
    def limit_ratios_latex(self):
        # TODO Extract method out to latex module
        return f"Flange: \n {self.flange.limit_ratio} \n Web: \n {self.web.limit_ratio}"


@dataclass
class DoublySymmetricIFlexuralMajorAxisSlendernessLatex:
    flange: DoublySymmetricIFlangeFlexuralMajorAxisSlendernessLatex
    web: DoublySymmetricIWebFlexuralSlendernessLatex

    @cached_property
    def limit_ratios_latex(self):
        # TODO Extract method out to latex module
        return f"""
            Flange: \n 
            {self.flange.slender_limit_ratio} \n
            {self.flange.compact_limit_ratio} \n 
            Web: \n 
            {self.web.slender_limit_ratio} \n
            {self.web.compact_limit_ratio}
        """


@dataclass
class DoublySymmetricISlendernessLatex:
    axial_compression: DoublySymmetricIAxialCompressionSlendernessLatex
    flexural_major_axis: DoublySymmetricIFlexuralMajorAxisSlendernessLatex


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
        return pd.concat((dimensions_table, area_properties_table, extra_table), axis=1)

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
        return FlangeWebSectionSlendernessDefaultImplementation(
            flange=DoublySymmetricIFlangeSlenderness(
                area_properties=self.area_properties,
                dimensions=self.dimensions,
                construction=self.construction,
                material=self.material
            ),
            web=DoublySymmetricIWebSlenderness(
                area_properties=self.area_properties,
                dimensions=self.dimensions,
                construction=self.construction,
                material=self.material
            )
        )

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


@dataclass
class DoublySymmetricIUserDefinedLatex:
    model: DoublySymmetricIUserDefined
    config_dict: ReportConfig = ReportConfig()

    @cached_property
    def limit_length_flexural_yield(self):
        return _process_quantity_entry_config(
            entry=self.model.limit_length_yield,
            print_config=self.config_dict.limit_length_flexural_yield
        )

    @cached_property
    def limit_length_flexural_yield_equation(self):
        return _limit_length_yield(
            minor_axis_radius_of_gyration=self.model.area_properties.latex.minor_axis_radius_of_gyration,
            modulus_linear=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_length=self.limit_length_flexural_yield
        )

    @cached_property
    def limit_length_flexural_lateral_torsional_buckling(self):
        return _process_quantity_entry_config(
            entry=self.model.limit_length_torsional_buckling,
            print_config=self.config_dict.limit_length_flexural_lateral_torsional_buckling
        )

    @cached_property
    def warping_constant(self):
        return _process_quantity_entry_config(
            entry=self.model.warping_constant,
            print_config=self.config_dict.warping_constant
        )

    @cached_property
    def effective_radius_of_gyration(self):
        return _process_quantity_entry_config(
            entry=self.model.effective_radius_of_gyration,
            print_config=self.config_dict.effective_radius_of_gyration
        )

    @cached_property
    def effective_radius_of_gyration_equation(self):
        return _effective_radius_of_gyration_equation(
            minor_axis_inertia=self.model.area_properties.latex.minor_axis_inertia,
            warping_constant=self.model.latex.warping_constant,
            major_axis_section_modulus=self.model.area_properties.latex.major_axis_elastic_section_modulus,
            effective_radius_of_gyration=self.effective_radius_of_gyration
        )

    @cached_property
    def coefficient_c(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.coefficient_c),
            print_config=self.config_dict.coefficient_c
        )

    @cached_property
    def limit_length_flexural_lateral_torsional_buckling_equation(self):
        return _limit_length_lateral_torsional_buckling(
            effective_radius_of_gyration=self.effective_radius_of_gyration,
            modulus_linear=self.model.material.latex.modulus_linear,
            yield_stress=self.model.material.latex.yield_stress,
            limit_length=self.limit_length_flexural_lateral_torsional_buckling,
            torsional_constant=self.model.area_properties.latex.torsional_constant,
            coefficient_c=self.coefficient_c,
            distance_between_centroids=self.model.dimensions.latex.distance_between_centroids,
            elastic_major_axis_section_modulus=self.model.area_properties.latex.major_axis_elastic_section_modulus
        )

    @cached_property
    def slenderness(self):
        axial_compression = DoublySymmetricIAxialCompressionSlendernessLatex(
            flange=DoublySymmetricIFlangeAxialCompressionSlendernessLatex(
                model=self.model.slenderness.flange
            ),
            web=DoublySymmetricIWebAxialCompressionSlendernessLatex(
                model=self.model.slenderness.web
            )
        )
        flexural_major_axis = DoublySymmetricIFlexuralMajorAxisSlendernessLatex(
            flange=DoublySymmetricIFlangeFlexuralMajorAxisSlendernessLatex(
                model=self.model.slenderness.flange
            ),
            web=DoublySymmetricIWebFlexuralSlendernessLatex(
                model=self.model.slenderness.web
            )
        )
        return DoublySymmetricISlendernessLatex(
            axial_compression=axial_compression,
            flexural_major_axis=flexural_major_axis
        )


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
    def calculation_memory(self):
        return BeamCompressionEffectiveLengthLatex(self)

    def axial_strength_ratio(self, required_axial_strength):
        return _axial_strength_ratio(
            required_axial_strength=required_axial_strength,
            available_axial_strength=self.design_strength
        )


@dataclass(frozen=True)
class BeamCompressionEffectiveLengthLatex:
    model: BeamCompressionEffectiveLength
    config_dict: ReportConfig = ReportConfig()
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    @cached_property
    def factor_k_minor_axis(self):
        return _process_quantity_entry_config(
            entry=self.model.factor_k_minor_axis,
            print_config=self.config_dict.factor_k
        )

    @cached_property
    def unbraced_length(self):
        return _process_quantity_entry_config(
            entry=self.model.unbraced_length,
            print_config=self.config_dict.unbraced_length
        )

    @cached_property
    def minor_axis_slenderness(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.minor_axis_slenderness),
            print_config=self.config_dict.minor_axis_slenderness
        )

    @cached_property
    def slenderness_limit(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.member_slenderness_limit),
            print_config=self.config_dict.slenderness_limit
        )

    @cached_property
    def minor_axis_slenderness_equation(self):
        slenderness_value = self.model.minor_axis_slenderness
        slenderness_limit = self.model.member_slenderness_limit
        inequality_sign = r"\leq" if slenderness_value <= slenderness_limit else ">"
        return _member_slenderness_minor_axis_flexural_bucking_latex(
            factor_k=self.factor_k_minor_axis,
            length=self.unbraced_length,
            radius_of_gyration=self.model.profile.area_properties.latex.minor_axis_radius_of_gyration,
            slenderness_value=self.minor_axis_slenderness,
            inequality_sign=inequality_sign,
            modulus=self.model.profile.material.latex.modulus_linear,
            slenderness_limit=self.slenderness_limit,
            yield_stress=self.model.profile.material.latex.yield_stress
        )

    @cached_property
    def elastic_flexural_buckling_stress(self):
        return _process_quantity_entry_config(
            entry=self.model.elastic_flexural_buckling_stress,
            print_config=self.config_dict.elastic_buckling_critical_stress
        )

    @cached_property
    def elastic_buckling_critical_stress_equation(self):
        return _elastic_buckling_critical_stress_latex(
            modulus=self.model.profile.material.latex.modulus_linear,
            length=self.unbraced_length,
            factor_k=self.factor_k_minor_axis,
            radius_of_gyration=self.model.profile.area_properties.latex.minor_axis_radius_of_gyration,
            elastic_buckling_critical_stress=self.elastic_flexural_buckling_stress,
        )

    @cached_property
    def flexural_buckling_critical_stress(self):
        return _process_quantity_entry_config(
            entry=self.model.flexural_buckling_critical_stress,
            print_config=self.config_dict.critical_stress
        )

    @cached_property
    def non_slender_critical_stress_lower_than(self):
        return _axial_compression_non_slender_critical_stress_lower_than(
            yield_stress=self.model.profile.material.latex.yield_stress,
            elastic_buckling_critical_stress=self.elastic_flexural_buckling_stress,
            critical_stress=self.flexural_buckling_critical_stress
        )

    @cached_property
    def non_slender_critical_stress_greater_than(self):
        return _axial_compression_non_slender_critical_stress_greater_than(
            yield_stress=self.model.profile.material.latex.yield_stress,
            elastic_buckling_critical_stress=self.elastic_flexural_buckling_stress,
            critical_stress=self.flexural_buckling_critical_stress
        )

    @cached_property
    def non_slender_critical_stress(self):
        if self.model.minor_axis_slenderness <= self.model.member_slenderness_limit:
            return self.non_slender_critical_stress_lower_than
        else:
            return self.non_slender_critical_stress_greater_than

    @cached_property
    def slender_critical_stress(self):
        return "Not implemented"

    @cached_property
    def strength_flexural_buckling(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_flexural_buckling,
            print_config=self.config_dict.strength_force
        )

    @cached_property
    def nominal_strength(self):
        return self.strength_flexural_buckling

    @cached_property
    def nominal_strength_equation(self):
        return _axial_compression_nominal_strength(
            critical_stress=self.flexural_buckling_critical_stress,
            area=self.model.profile.area_properties.latex.area,
            nominal_strength=self.strength_flexural_buckling,

        )

    @cached_property
    def design_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.design_strength,
            print_config=self.config_dict.strength_force
        )

    @cached_property
    def design_strength_equation(self):
        return _design_strength(
            nominal_strength=self.nominal_strength,
            safety_factor=str(self.safety_factor.value),
            design_strength=self.design_strength,
            safety_factor_type=self.safety_factor,
            strength_type="force"
        )

    @cached_property
    def resume(self):
        string = CONCATENATE_STRING
        return string.join(
            (
                self.model.profile.latex.slenderness.axial_compression.limit_ratios_latex,
                self.minor_axis_slenderness_equation,
                self.elastic_buckling_critical_stress_equation,
                self.non_slender_critical_stress,
                self.nominal_strength_equation,
                self.design_strength_equation
            )
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

    def strength_lateral_torsion_compact_case_b(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_b(
            length_between_braces=self.unbraced_length,
            limiting_length_torsional_buckling=self.profile.limit_length_torsional_buckling,
            limiting_length_yield=self.profile.limit_length_yield,
            mod_factor=mod_factor,
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            yield_stress=self.profile.material.yield_stress
        )

    def critical_stress_lateral_torsional_buckling(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_critical_stress_compact_doubly_symmetric(
            mod_factor=mod_factor,
            length_between_braces=self.unbraced_length,
            modulus=self.profile.material.modulus_linear,
            coefficient_c=self.profile.coefficient_c,
            distance_between_flange_centroids=self.profile.dimensions.distance_between_centroids,
            effective_radius_of_gyration=self.profile.effective_radius_of_gyration,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            torsional_constant=self.profile.area_properties.torsional_constant
        )

    def strength_lateral_torsion_compact_case_c(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength_compact_doubly_symmetric_case_c(
            plastic_moment=self.plastic_moment_major_axis,
            section_modulus=self.profile.area_properties.major_axis_elastic_section_modulus,
            critical_stress=self.critical_stress_lateral_torsional_buckling(mod_factor),
        )

    def strength_lateral_torsion(self, mod_factor: float = 1.) -> Quantity:
        return _flexural_lateral_torsional_buckling_strength(
            case_b=self.strength_lateral_torsion_compact_case_b(mod_factor),
            case_c=self.strength_lateral_torsion_compact_case_c(mod_factor),
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

    def nominal_strength_major_axis(self, mod_factor: float = 1.) -> Quantity:
        yield_ = self.strength_major_axis_yield
        lateral_torsional_buckling = self.strength_lateral_torsion(mod_factor)
        flange_local_buckling = self.strength_major_axis_flange_local_buckling
        strengths = (yield_, lateral_torsional_buckling, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    def nominal_strength_minor_axis(self, mod_factor: float = 1.) -> Quantity:
        yield_ = self.strength_minor_axis_yield
        flange_local_buckling = self.strength_minor_axis_flange_local_buckling
        strengths = (yield_, flange_local_buckling)
        return _minimum_allowed_strength(strengths)

    def design_strength_major_axis(self, mod_factor=1.) -> Quantity:
        return self.safety_factor.allowable_value(self.nominal_strength_major_axis(mod_factor=mod_factor))

    def design_strength_minor_axis(self, mod_factor=1.) -> Quantity:
        return self.safety_factor.allowable_value(self.nominal_strength_minor_axis(mod_factor=mod_factor))

    def strength_resume(self, mod_factor: float = 1.) -> pd.DataFrame:
        strength_local_buckling = self.strength_major_axis_flange_local_buckling
        df = {
            "strength yield": [self.safety_factor.allowable_value(self.strength_major_axis_yield)],
            "strength lateral torsion": [
                self.safety_factor.allowable_value(
                    self.strength_lateral_torsion(mod_factor=mod_factor)
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
    def calculation_memory(self):
        return BeamFlexureDoublySymmetricLatex(self)


@dataclass
class BeamFlexureDoublySymmetricLatex:
    model: BeamFlexureDoublySymmetric

    @cached_property
    def major_axis(self):
        return BeamFlexureMajorAxisDoublySymmetricLatex(self.model)

    @cached_property
    def minor_axis(self):
        return BeamFlexureMinorAxisDoublySymmetricLatex(self.model)


@dataclass
class BeamFlexureMajorAxisDoublySymmetricLatex:
    model: BeamFlexureDoublySymmetric
    config_dict: ReportConfig = ReportConfig()

    def resume(self, mod_factor: float):
        title = "Major axis"
        string = CONCATENATE_STRING
        return string.join(
            (
                title,
                self.model.profile.latex.slenderness.flexural_major_axis.limit_ratios_latex,
                self.yield_strength_equation,
                self.model.profile.latex.limit_length_flexural_yield_equation,
                self.model.profile.latex.effective_radius_of_gyration_equation,
                self.model.profile.latex.limit_length_flexural_lateral_torsional_buckling_equation,
                self.lateral_torsional_buckling_strength_equation(mod_factor=mod_factor) or "",
                self.design_strength_equation(mod_factor=mod_factor)
            )
        )

    @cached_property
    def yield_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_major_axis_yield,
            print_config=self.config_dict.strength_moment
        )

    @cached_property
    def yield_strength_equation(self):
        return _flexural_yield_nominal_strength(
            yield_stress=self.model.profile.material.latex.yield_stress,
            plastic_section_modulus=self.model.profile.area_properties.latex.major_axis_plastic_section_modulus,
            nominal_strength=self.yield_strength,
            axis="major"
        )

    def mod_factor(self, mod_factor: float):
        return _process_quantity_entry_config(
            entry=mod_factor,
            print_config=self.config_dict.mod_factor
        )

    @cached_property
    def unbraced_length(self):
        return _process_quantity_entry_config(
            entry=self.model.unbraced_length,
            print_config=self.config_dict.unbraced_length
        )

    def lateral_torsional_buckling_strength_case_b(self, mod_factor: float):
        return _process_quantity_entry_config(
            entry=self.model.strength_lateral_torsion_compact_case_b(mod_factor=mod_factor),
            print_config=self.config_dict.strength_moment
        )

    def lateral_torsional_buckling_strength_case_b_equation(self, mod_factor: float):
        return _flexural_lateral_torsional_buckling_strength_case_b(
            mod_factor=self.mod_factor(mod_factor),
            yield_stress=self.model.profile.material.latex.yield_stress,
            plastic_moment=self.yield_strength,
            elastic_major_axis_section_modulus=self.model.profile.area_properties.latex
                .major_axis_elastic_section_modulus,
            unbraced_length=self.unbraced_length,
            limit_length_yield=self.model.profile.latex.limit_length_flexural_yield,
            limit_length_lateral_torsional_buckling=self.model.profile.latex
                .limit_length_flexural_lateral_torsional_buckling,
            nominal_strength=self.lateral_torsional_buckling_strength_case_b(mod_factor=mod_factor)
        )

    def lateral_torsional_buckling_strength_equation(self, mod_factor: float) -> str | None:
        # TODO implement case c and check which case is appropriate
        return _flexural_lateral_torsional_buckling_strength(
            case_b=self.lateral_torsional_buckling_strength_case_b_equation(mod_factor=mod_factor),
            case_c="Case c: Not Implemented",
            length_between_braces=self.model.unbraced_length,
            limiting_length_yield=self.model.profile.limit_length_yield,
            limiting_length_torsional_buckling=self.model.profile.limit_length_torsional_buckling
        )

    def nominal_strength(self, mod_factor: float):
        return _process_quantity_entry_config(
            entry=self.model.nominal_strength_major_axis(mod_factor=mod_factor),
            print_config=self.config_dict.strength_moment
        )

    def design_strength(self, mod_factor: float):
        return _process_quantity_entry_config(
            entry=self.model.design_strength_major_axis(mod_factor=mod_factor),
            print_config=self.config_dict.strength_moment
        )

    def design_strength_equation(self, mod_factor: float):
        return _design_strength(
            nominal_strength=self.nominal_strength(mod_factor=mod_factor),
            safety_factor_type=self.model.safety_factor,
            safety_factor=str(self.model.safety_factor.value),
            design_strength=self.design_strength(mod_factor=mod_factor),
            strength_type="moment"
        )


@dataclass
class BeamFlexureMinorAxisDoublySymmetricLatex:
    model: BeamFlexureDoublySymmetric
    config_dict: ReportConfig = ReportConfig()

    def resume(self, mod_factor: float):
        title = "Minor axis"
        string = CONCATENATE_STRING
        return string.join(
            (
                title,
                self.yield_strength_equation,
                self.design_strength_equation(mod_factor=mod_factor)
            )
        )

    @cached_property
    def yield_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_minor_axis_yield,
            print_config=self.config_dict.strength_moment
        )

    @cached_property
    def yield_strength_equation(self):
        return _flexural_yield_nominal_strength(
            yield_stress=self.model.profile.material.latex.yield_stress,
            plastic_section_modulus=self.model.profile.area_properties.latex.minor_axis_plastic_section_modulus,
            nominal_strength=self.yield_strength,
            axis="minor"
        )

    def nominal_strength(self, mod_factor: float):
        return _process_quantity_entry_config(
            entry=self.model.nominal_strength_minor_axis(mod_factor=mod_factor),
            print_config=self.config_dict.strength_moment
        )

    def design_strength(self, mod_factor: float):
        return _process_quantity_entry_config(
            entry=self.model.design_strength_minor_axis(mod_factor=mod_factor),
            print_config=self.config_dict.strength_moment
        )

    def design_strength_equation(self, mod_factor: float):
        return _design_strength(
            nominal_strength=self.nominal_strength(mod_factor=mod_factor),
            safety_factor_type=self.model.safety_factor,
            safety_factor=str(self.model.safety_factor.value),
            design_strength=self.design_strength(mod_factor=mod_factor),
            strength_type="moment"
        )


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLength:
    profile: DoublySymmetricIUserDefined
    unbraced_length: Quantity
    factor_k_minor_axis: float = 1.0
    factor_k_major_axis: float = 1.0
    factor_k_torsion: float = 1.0
    safety_factor: SafetyFactor = AllowableStrengthDesign()

    def stand_alone_report(
            self,
            required_axial_strength: Quantity,
            required_major_axis_flexure_strength: Quantity,
            required_minor_axis_flexure_strength: Quantity,
            lateral_torsional_buckling_modification_factor: float = 1.
    ):
        material = self.profile.material.data_table_latex
        area_properties = self.profile.area_properties.data_table_latex
        compression = self.compression.calculation_memory.resume
        flexure_major_axis = self.flexure.calculation_memory.major_axis.resume(
            mod_factor=lateral_torsional_buckling_modification_factor
        )
        flexure_minor_axis = self.flexure.calculation_memory.minor_axis.resume(
            mod_factor=lateral_torsional_buckling_modification_factor
        )
        string = CONCATENATE_STRING
        document_string = string.join(
            (
                material,
                area_properties,
                compression,
                flexure_major_axis,
                flexure_minor_axis
            )
        )
        return _build_doc(document_string)

    @cached_property
    def compression(self):
        return BeamCompressionEffectiveLength(
            profile=self.profile,
            unbraced_length=self.unbraced_length,
            factor_k_torsion=self.factor_k_torsion,
            factor_k_major_axis=self.factor_k_major_axis,
            factor_k_minor_axis=self.factor_k_minor_axis
        )

    @cached_property
    def flexure(self):
        return BeamFlexureDoublySymmetric(
            profile=self.profile,
            unbraced_length=self.unbraced_length,
        )

    def compression_flexure_combined_criteria_h1_1(
            self,
            required_axial_strength: Quantity,
            required_major_axis_flexure_strength: Quantity,
            required_minor_axis_flexure_strength: Quantity,
            lateral_torsional_buckling_modification_factor: float = 1.
    ) -> float:
        available_axial_strength = self.compression.design_strength
        available_major_axis_strength = self.flexure.design_strength_major_axis(
            mod_factor=lateral_torsional_buckling_modification_factor
        )
        available_minor_axis_strength = self.flexure.design_strength_minor_axis(
            mod_factor=lateral_torsional_buckling_modification_factor
        )
        return _flexure_and_axial_compression_h1_1_criteria(
            available_axial_strength=available_axial_strength,
            required_axial_strength=required_axial_strength,
            available_major_axis_flexural_strength=available_major_axis_strength,
            required_major_axis_flexural_strength=required_major_axis_flexure_strength,
            available_minor_axis_flexural_strength=available_minor_axis_strength,
            required_minor_axis_flexural_strength=required_minor_axis_flexure_strength,
        )

    def resume(self, mod_factor=1.):
        return pd.concat((self.compression.strength_resume, self.flexure.strength_resume(mod_factor)), axis=1)

    @cached_property
    def latex(self):
        return BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex(self)


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex:
    model: BeamCompressionFlexureDoublySymmetricEffectiveLength
    config_dict: ReportConfig = ReportConfig()

    def stand_alone_report(
            self,
            required_axial_strength: Quantity,
            required_major_axis_flexure_strength: Quantity,
            required_minor_axis_flexure_strength: Quantity,
            lateral_torsional_buckling_modification_factor: float = 1.
    ):
        material = self.model.profile.material.data_table_latex
        area_properties = self.model.profile.area_properties.data_table_latex
        compression = self.model.compression.calculation_memory.resume
        flexure_major_axis = self.model.flexure.calculation_memory.major_axis.resume(
            mod_factor=lateral_torsional_buckling_modification_factor
        )
        flexure_minor_axis = self.model.flexure.calculation_memory.minor_axis.resume(
            mod_factor=lateral_torsional_buckling_modification_factor
        )
        string = CONCATENATE_STRING
        document_string = string.join(
            (
                material,
                area_properties,
                compression,
                flexure_major_axis,
                flexure_minor_axis
            )
        )
        return _build_doc(document_string)

    def flexure_compression_h1_criteria(
            self,
            required_axial_strength: Quantity,
            required_major_axis_flexure_strength: Quantity,
            required_minor_axis_flexure_strength: Quantity,
            lateral_torsional_buckling_modification_factor: float = 1.
    ):
        return _process_quantity_entry_config(
            entry=self.model.compression_flexure_combined_criteria_h1_1(
                required_axial_strength=required_axial_strength,
                required_minor_axis_flexure_strength=required_minor_axis_flexure_strength,
                required_major_axis_flexure_strength=required_major_axis_flexure_strength,
                lateral_torsional_buckling_modification_factor=lateral_torsional_buckling_modification_factor
            ),
            print_config=self.config_dict.criteria
        )

    def flexure_compression_h1_criteria_equation(
            self,
            required_axial_strength: Quantity,
            required_major_axis_flexure_strength: Quantity,
            required_minor_axis_flexure_strength: Quantity,
            lateral_torsional_buckling_modification_factor: float = 1.
    ):
        criteria = self.flexure_compression_h1_criteria(
            required_major_axis_flexure_strength=required_major_axis_flexure_strength,
            required_axial_strength=required_axial_strength,
            required_minor_axis_flexure_strength=required_minor_axis_flexure_strength,
            lateral_torsional_buckling_modification_factor=lateral_torsional_buckling_modification_factor
        )
        axial_strength_ratio_value = self.model.compression.axial_strength_ratio(
            required_axial_strength=required_axial_strength
        )
        if axial_strength_ratio_value < 0.2:
            axial_strength_ratio = "lower_than_0_2"
        else:
            axial_strength_ratio = "greater_than_0_2"
        return
        # return _flexure_compression_h1_criteria_equation(
        #     axial_strength_ratio=axial_strength_ratio,
        #                           required_axial_strength=,
        # design_axial_strength: str,
        # required_flexural_major_axis_strength: str,
        # design_strength_flexural_major_axis: str,
        # required_flexural_minor_axis_strength: str,
        # design_strength_flexural_minor_axis: str,
        # criteria: str
        # )
