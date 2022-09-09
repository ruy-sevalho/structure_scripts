import pathlib
from dataclasses import dataclass
from functools import cached_property
from itertools import chain

from pylatex import NoEscape, Section, Subsection, Subsubsection, Document
from quantities import Quantity

from structure_scripts.aisc_360_10.latex_helpers import (
    _slenderness_default_limit_ratio_latex, _member_slenderness_minor_axis_flexural_bucking_latex,
    _dataframe_table_columns, _elastic_buckling_critical_stress_latex,
    _axial_compression_non_slender_critical_stress_lower_than,
    _axial_compression_non_slender_critical_stress_greater_than, _axial_compression_nominal_strength,
    _process_quantity_entry_config, _design_strength_asd, _design_strength_lfrd, _design_strength,
    _flexural_yield_nominal_strength, _limit_length_yield, _limit_length_lateral_torsional_buckling,
    _flexural_lateral_torsional_buckling_strength_case_b, _build_doc, CONCATENATE_STRING,
    _effective_radius_of_gyration_equation, _flexure_compression_h1_criteria_equation, _axial_strength_ratio_equation,
    _ratio_equation, _build_single_element, standard_wrapper, Multline, Split, env, _axial_slenderness_result,
    _flexural_slenderness_result
)
from structure_scripts.aisc_360_10.helpers import ConstructionType, _flexural_lateral_torsional_buckling_strength
from structure_scripts.aisc_360_10.report_config import ReportConfig

from typing import TYPE_CHECKING, Collection, Any

if TYPE_CHECKING:
    from structure_scripts.aisc_360_10 import (
        Material,
        AreaProperties,
        DoublySymmetricIDimensions,
        DoublySymmetricIUserDefined,
        DoublySymmetricIWebSlenderness,
        DoublySymmetricIFlangeSlenderness,
        DoublySymmetricIDimensionsUserDefined,
        DoublySymmetricIUserDefinedFlangeWebSectionSlenderness,
        BeamCompressionEffectiveLength,
        BeamFlexureDoublySymmetric,
        BeamCompressionFlexureDoublySymmetricEffectiveLength
    )

config_dict = ReportConfig()
SLENDERNESS_LIMIT_TITLE = "Limites de Esbeltez"
SLENDER_NON_SLENDER_LIMIT_DESCRIPTION = NoEscape(r"Raz\~ao de esbletez limite n\~ao esbelto / esbelto:")
COMPACT_NON_COMPACT_LIMIT_DESCRIPTION = NoEscape(r"Raz\~ao de esbletez limite compacto / n\~ao compacto:")
NON_COMPACT_SLENDER_LIMIT_DESCRIPTION = NoEscape(r"Raz\~ao de esbletez limite n\~ao compacto / esbelto:")


def save_single_entry(content: str, file_name: str):
    path = pathlib.Path(r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\pdf_maker\tex_files") / file_name
    content = _build_single_element(content)
    with open(path, "w") as f:
        f.write(content)


def insert_between(collection: Collection[Any], separator: str = "\n"):
    col = ((item, separator) for item in collection)
    return list(chain(*col))


@dataclass
class MaterialLatex:
    material: "Material"

    def resume(self):
        save_single_entry(
            content=self.data_table,
            file_name="shared.tex"
        )

    @cached_property
    def resume_latex(self):
        return Section(
            title="Material",
            data=self.data_table_latex
        )

    @cached_property
    def data_table_latex(self):
        return _dataframe_table_columns(
            df=self.material.data_table_df,
            unit_display="cell",
            include_description=True
        )

    @cached_property
    def data_table(self):
        return _dataframe_table_columns(
            df=self.material.data_table_df,
            unit_display="cell",
            include_description=True
        ).dumps()

    @cached_property
    def modulus_linear(self):
        return _process_quantity_entry_config(
            entry=self.material.modulus_linear,
            print_config=config_dict.modulus_linear
        )

    @cached_property
    def modulus_shear(self):
        return _process_quantity_entry_config(
            entry=self.material.modulus_shear,
            print_config=config_dict.modulus_shear
        )

    @cached_property
    def yield_stress(self):
        return _process_quantity_entry_config(
            entry=self.material.yield_stress,
            print_config=config_dict.yield_stress
        )


@dataclass
class AreaPropertiesLatex:
    data: "AreaProperties"

    @cached_property
    def area(self):
        return _process_quantity_entry_config(
            entry=self.data.area,
            print_config=config_dict.area
        )

    @cached_property
    def major_axis_inertia(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_inertia,
            print_config=config_dict.major_axis_inertia
        )

    @cached_property
    def major_axis_elastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_elastic_section_modulus,
            print_config=config_dict.major_axis_elastic_section_modulus
        )

    @cached_property
    def major_axis_plastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_plastic_section_modulus,
            print_config=config_dict.major_axis_plastic_section_modulus
        )

    @cached_property
    def major_axis_radius_of_gyration(self):
        return _process_quantity_entry_config(
            entry=self.data.major_axis_radius_of_gyration,
            print_config=config_dict.major_axis_radius_of_gyration
        )

    @cached_property
    def minor_axis_inertia(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_inertia,
            print_config=config_dict.minor_axis_inertia
        )

    @cached_property
    def minor_axis_elastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_elastic_section_modulus,
            print_config=config_dict.minor_axis_elastic_section_modulus
        )

    @cached_property
    def minor_axis_plastic_section_modulus(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_plastic_section_modulus,
            print_config=config_dict.minor_axis_plastic_section_modulus
        )

    @cached_property
    def minor_axis_radius_of_gyration(self):
        return _process_quantity_entry_config(
            entry=self.data.minor_axis_radius_of_gyration,
            print_config=config_dict.minor_axis_radius_of_gyration
        )

    @cached_property
    def torsional_constant(self):
        return _process_quantity_entry_config(
            entry=self.data.torsional_constant,
            print_config=config_dict.torsional_constant
        )

    @cached_property
    def torsional_constant(self):
        return _process_quantity_entry_config(
            entry=self.data.torsional_constant,
            print_config=config_dict.torsional_constant
        )

    @cached_property
    def warping_constant(self):
        return _process_quantity_entry_config(
            entry=self.data.warping_constant,
            print_config=config_dict.warping_constant
        )


@dataclass
class DoublySymmetricIDimensionsLatex:
    model: "DoublySymmetricIDimensions"

    @cached_property
    def distance_between_centroids(self):
        return _process_quantity_entry_config(
            entry=self.model.distance_between_centroids,
            print_config=config_dict.distance_between_centroids
        )

    @cached_property
    def flange_thickness(self):
        return _process_quantity_entry_config(
            entry=self.model.flange_thickness,
            print_config=config_dict.flange_thickness,
        )

    @cached_property
    def flange_width(self):
        return _process_quantity_entry_config(
            entry=self.model.flange_width,
            print_config=config_dict.flange_width,
        )

    @cached_property
    def web_thickness(self):
        return _process_quantity_entry_config(
            entry=self.model.web_thickness,
            print_config=config_dict.web_thickness,
        )

    @cached_property
    def web_height(self):
        return _process_quantity_entry_config(
            entry=self.model.web_height,
            print_config=config_dict.web_height,
        )


@dataclass
class DoublySymmetricIFlangeAxialCompressionSlendernessLatex:
    model: "DoublySymmetricIFlangeSlenderness"

    @cached_property
    def ratio(self):
        return _process_quantity_entry_config(
            entry=self.model.ratio,
            print_config=config_dict.flange_slenderness
        )

    @cached_property
    def ratio_equation(self):
        return _ratio_equation(
            numerator_symbol=config_dict.flange_width.label[1:-1],
            numerator_value=self.model.profile.dimensions.latex.flange_width[1:-1],
            denominator_symbol=f"2{config_dict.flange_thickness[1:-1]}",
            denominator_value=self.model.profile.dimensions.latex.flange_thickness,
            ratio_symbol=config_dict.flange_slenderness.label[1:-1],
            ratio_value=self.ratio
        )

    @cached_property
    def axial_limit_ratio_rolled(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.axial_limit_ratio_rolled),
            print_config=config_dict.slender_limit_ratio
        )

    @cached_property
    def slender_limit_ratio_rolled(self):
        return _slenderness_default_limit_ratio_latex(
            factor="0.56",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
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
        return table[self.model.profile.construction]

    @cached_property
    def slenderness_result(self):
        return _axial_slenderness_result(
            slenderness=self.model.axial_compression_value,
            element="flange"
        )

    def resume(self):
        save_single_entry(
            content=self.limit_ratio,
            file_name="comp_flange_slender_limit.tex"
        )

    @cached_property
    def resume_latex(self):
        return Subsubsection(
            title="Flange",
            data=[SLENDER_NON_SLENDER_LIMIT_DESCRIPTION, NoEscape(self.limit_ratio), NoEscape(self.slenderness_result)]
        )


@dataclass
class DoublySymmetricIFlangeFlexuralMajorAxisSlendernessLatex:
    model: "DoublySymmetricIFlangeSlenderness"

    @cached_property
    def flexural_slender_limit_ratio_rolled(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_slender_limit_ratio_rolled),
            print_config=config_dict.slender_limit_ratio
        )

    @cached_property
    def slender_limit_ratio_rolled(self):
        return _slenderness_default_limit_ratio_latex(
            factor="1.0",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
            limit_ratio=self.flexural_slender_limit_ratio_rolled,
            limit_ratio_type="slender"
        )

    @cached_property
    def flexural_major_axis_compact_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_major_axis.compact_limit_ratio),
            print_config=config_dict.compact_limit_ratio
        )

    @cached_property
    def compact_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="0.38",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
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
        return table[self.model.profile.construction]

    @cached_property
    def slenderness_result(self):
        return _flexural_slenderness_result(
            slenderness=self.model.flexural_major_axis_value,
            element="flange"
        )

    def resume(self):
        save_single_entry(
            content=self.slender_limit_ratio,
            file_name="flex_major_axis_flange_slender_limit_ratio.tex"
        )
        save_single_entry(
            content=self.compact_limit_ratio,
            file_name="flex_major_axis_flange_compact_limit_ratio.tex"
        )

    @cached_property
    def resume_latex(self):
        return Subsubsection(
            title="Flange",
            data=insert_between(
                [
                    COMPACT_NON_COMPACT_LIMIT_DESCRIPTION,
                    NoEscape(self.slender_limit_ratio),
                    NON_COMPACT_SLENDER_LIMIT_DESCRIPTION,
                    NoEscape(self.compact_limit_ratio),
                    NoEscape(self.slenderness_result)
                ]
            )
        )


@dataclass
class DoublySymmetricIFlangeFlexuralMinorAxisSlendernessLatex:
    model: "DoublySymmetricIFlangeSlenderness"

    @cached_property
    def flexural_minor_axis_slender_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_minor_axis.slender_limit_ratio),
            print_config=config_dict.slender_limit_ratio
        )

    @cached_property
    def flexural_minor_axis_compact_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_minor_axis.compact_limit_ratio),
            print_config=config_dict.compact_limit_ratio
        )

    @cached_property
    def slender_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="1.0",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
            limit_ratio=self.flexural_minor_axis_slender_limit_ratio,
            limit_ratio_type="slender"
        )

    @cached_property
    def compact_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="0.38",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
            limit_ratio=self.flexural_minor_axis_compact_limit_ratio,
            limit_ratio_type="compact"
        )

    @cached_property
    def slenderness_result(self):
        return _flexural_slenderness_result(
            slenderness=self.model.flexural_minor_axis_value,
            element="flange"
        )

    def resume(self):
        save_single_entry(
            content=(self.slender_limit_ratio),
            file_name="flex_minor_axis_flange_slender_limit_ratio.tex"
        )
        save_single_entry(
            content=self.compact_limit_ratio,
            file_name="flex_minor_axis_flange_compact_limit_ratio.tex"
        )
        return f"{self.slender_limit_ratio} \n {self.compact_limit_ratio}"

    @cached_property
    def resume_latex(self):
        return Subsubsection(
            title="Flange",
            data=insert_between(
                [
                    COMPACT_NON_COMPACT_LIMIT_DESCRIPTION,
                    NoEscape(self.slender_limit_ratio),
                    NON_COMPACT_SLENDER_LIMIT_DESCRIPTION,
                    NoEscape(self.compact_limit_ratio),
                    NoEscape(self.slenderness_result)
                ]
            )
        )


@dataclass
class DoublySymmetricIWebAxialCompressionSlendernessLatex:
    model: "DoublySymmetricIWebSlenderness"

    @cached_property
    def axial_compression_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.axial_compression.limit_ratio),
            print_config=config_dict.compact_limit_ratio
        )

    @cached_property
    def limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="1.49",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
            limit_ratio=self.axial_compression_limit_ratio,
            limit_ratio_type="slender"
        )

    def resume(self):
        save_single_entry(
            content=self.limit_ratio,
            file_name="comp_web_slender_limit.tex"
        )

    @cached_property
    def slenderness_result(self):
        return _axial_slenderness_result(
            slenderness=self.model.axial_compression_value,
            element="web"
        )

    @cached_property
    def resume_latex(self):
        return Subsubsection(
            title="Alma",
            data=[NoEscape(self.limit_ratio), NoEscape(self.slenderness_result)]
        )


@dataclass
class DoublySymmetricIWebFlexuralSlendernessLatex:
    model: "DoublySymmetricIWebSlenderness"

    @cached_property
    def flexural_slender_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_slender_limit_ratio),
            print_config=config_dict.slender_limit_ratio
        )

    @cached_property
    def flexural_compact_limit_ratio(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.flexural_compact_limit_ratio),
            print_config=config_dict.compact_limit_ratio
        )

    @cached_property
    def slender_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="3.76",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
            limit_ratio=self.flexural_slender_limit_ratio,
            limit_ratio_type="slender"
        )

    @cached_property
    def compact_limit_ratio(self):
        return _slenderness_default_limit_ratio_latex(
            factor="5.70",
            modulus=self.model.profile.material.latex.modulus_linear,
            yield_stress=self.model.profile.material.latex.yield_stress,
            limit_ratio=self.flexural_compact_limit_ratio,
            limit_ratio_type="compact"
        )

    @cached_property
    def slenderness_results(self):
        return _flexural_slenderness_result(
            slenderness=self.model.flexural_value,
            element="web"
        )

    def resume(self):
        save_single_entry(
            content=self.slender_limit_ratio,
            file_name="flex_web_slender_limit_ratio.tex"
        )
        save_single_entry(
            content=self.compact_limit_ratio,
            file_name="flex_web_compact_limit_ratio.tex"
        )

    @cached_property
    def resume_latex(self):
        return Subsubsection(
            title="Alma",
            data=insert_between(
                [
                    NoEscape(self.slender_limit_ratio),
                    NoEscape(self.compact_limit_ratio),
                    NoEscape(self.slenderness_results)
                ]
            )
        )


@dataclass
class DoublySymmetricIAxialCompressionSlendernessLatex:
    model: "DoublySymmetricIUserDefinedFlangeWebSectionSlenderness"

    @cached_property
    def flange(self):
        return DoublySymmetricIFlangeAxialCompressionSlendernessLatex(
            model=self.model.flange
        )

    @cached_property
    def web(self):
        return DoublySymmetricIWebAxialCompressionSlendernessLatex(
            model=self.model.web
        )

    def resume(self):
        self.flange.resume()
        self.web.resume()

    @cached_property
    def resume_latex(self):
        return Subsection(
            title=SLENDERNESS_LIMIT_TITLE,
            data=[
                self.flange.resume_latex,
                self.web.resume_latex
            ]
        )


@dataclass
class DoublySymmetricIFlexuralMajorAxisSlendernessLatex:
    model: "DoublySymmetricIUserDefinedFlangeWebSectionSlenderness"

    @cached_property
    def flange(self):
        return DoublySymmetricIFlangeFlexuralMajorAxisSlendernessLatex(
            model=self.model.flange
        )

    @cached_property
    def web(self):
        return DoublySymmetricIWebFlexuralSlendernessLatex(
            model=self.model.web
        )

    def resume(self):
        self.flange.resume()
        self.web.resume()

    @cached_property
    def resume_latex(self):
        return Subsection(
            title=SLENDERNESS_LIMIT_TITLE,
            data=[
                self.flange.resume_latex,
                self.web.resume_latex
            ]
        )


@dataclass
class DoublySymmetricIFlexuralMinorAxisSlendernessLatex:
    model: "DoublySymmetricIUserDefinedFlangeWebSectionSlenderness"

    @cached_property
    def flange(self):
        return DoublySymmetricIFlangeFlexuralMinorAxisSlendernessLatex(
            model=self.model.flange
        )

    @cached_property
    def web(self):
        return DoublySymmetricIWebFlexuralSlendernessLatex(
            model=self.model.web
        )

    def resume(self):
        self.flange.resume()
        self.web.resume()

    @cached_property
    def resume_latex(self):
        return Subsection(
            title=SLENDERNESS_LIMIT_TITLE,
            data=[
                self.flange.resume_latex,
                self.web.resume_latex
            ]
        )


@dataclass
class DoublySymmetricISlendernessLatex:
    model: "DoublySymmetricIUserDefinedFlangeWebSectionSlenderness"

    @cached_property
    def flange_slenderness(self):
        return _process_quantity_entry_config(
            entry=self.model.flange.ratio,
            print_config=config_dict.flange_slenderness
        )

    @cached_property
    def flange_slenderness_equation(self):
        return _ratio_equation(
            numerator_symbol=config_dict.flange_width.label[1:-1],
            numerator_value=self.model.profile.dimensions.latex.flange_width,
            denominator_symbol=f"2{config_dict.flange_thickness.label[1:-1]}",
            denominator_value="2 " + r"\cdot " + self.model.profile.dimensions.latex.flange_thickness,
            ratio_symbol=config_dict.flange_slenderness.label[1:-1],
            ratio_value=self.flange_slenderness
        )

    @cached_property
    def web_slenderness(self):
        return _process_quantity_entry_config(
            entry=self.model.web.ratio,
            print_config=config_dict.web_slenderness
        )

    @cached_property
    def web_slenderness_equation(self):
        return _ratio_equation(
            numerator_symbol=config_dict.web_height.label[1:-1],
            numerator_value=self.model.profile.dimensions.latex.web_height,
            denominator_symbol=config_dict.web_thickness.label[1:-1],
            denominator_value=self.model.profile.dimensions.latex.web_thickness,
            ratio_symbol=config_dict.web_slenderness.label[1:-1],
            ratio_value=self.web_slenderness
        )

    @cached_property
    def axial_compression(self):
        return DoublySymmetricIAxialCompressionSlendernessLatex(self.model)

    @cached_property
    def flexural_major_axis(self):
        return DoublySymmetricIFlexuralMajorAxisSlendernessLatex(self.model)

    @cached_property
    def flexural_minor_axis(self):
        return DoublySymmetricIFlexuralMinorAxisSlendernessLatex(self.model)

    def resume_ratios(self):
        save_single_entry(
            content=self.flange_slenderness_equation,
            file_name="flange_slenderness_ratio.tex"
        )
        save_single_entry(
            content=self.web_slenderness,
            file_name="web_slenderness_ratio.tex"
        )

    @cached_property
    def resume_latex(self):
        flange = Subsubsection(
            title="Flange",
            data=NoEscape(self.flange_slenderness_equation)
        )
        web = Subsubsection(
            title="Alma",
            data=NoEscape(self.web_slenderness_equation)
        )
        return Subsection(
            title=NoEscape(r"Raz\~oes de Esbeltez"),
            data=[
                flange,
                web
            ]
        )


@dataclass
class DoublySymmetricIUserDefinedLatex:
    model: "DoublySymmetricIUserDefined"

    @cached_property
    def data_table(self):
        return _dataframe_table_columns(
            df=self.model.default_table,
            unit_display="cell",
            include_description=True
        ).dumps()

    @cached_property
    def data_table_latex(self):
        return _dataframe_table_columns(
            df=self.model.default_table,
            unit_display="cell",
            include_description=True
        )

    def resume(self):
        save_single_entry(
            content=self.data_table,
            file_name="profile.tex"
        )
        save_single_entry(
            content=(self.slenderness.flange_slenderness_equation),
            file_name="flange_slenderness_ratio.tex"
        )
        save_single_entry(
            content=(self.slenderness.web_slenderness_equation),
            file_name="web_slenderness_ratio.tex"
        )

    @cached_property
    def resume_latex(self):
        return Section(
            title="Perfil",
            data=insert_between(
                [
                    self.data_table_latex,
                    self.slenderness.resume_latex,
                ]
            )
        )

    @cached_property
    def limit_length_flexural_yield(self):
        return _process_quantity_entry_config(
            entry=self.model.limit_length_yield,
            print_config=config_dict.limit_length_flexural_yield
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
            print_config=config_dict.limit_length_flexural_lateral_torsional_buckling
        )

    @cached_property
    def warping_constant(self):
        return _process_quantity_entry_config(
            entry=self.model.warping_constant,
            print_config=config_dict.warping_constant
        )

    @cached_property
    def effective_radius_of_gyration(self):
        return _process_quantity_entry_config(
            entry=self.model.effective_radius_of_gyration,
            print_config=config_dict.effective_radius_of_gyration
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
            print_config=config_dict.coefficient_c
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
        return DoublySymmetricISlendernessLatex(
            model=self.model.slenderness
        )


@dataclass
class BeamCompressionEffectiveLengthLatex:
    model: "BeamCompressionEffectiveLength"

    @cached_property
    def required_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.required_strength,
            print_config=config_dict.strength_force
        )

    @cached_property
    def axial_strength_ratio(self):
        return _process_quantity_entry_config(
            entry=self.model.axial_strength_ratio,
            print_config=config_dict.criteria
        )

    @cached_property
    def axial_strength_ratio_equation(self):
        return _axial_strength_ratio_equation(
            required_strength=self.required_strength,
            design_strength=self.design_strength,
            ratio=self.axial_strength_ratio
        )

    @cached_property
    def factor_k_minor_axis(self):
        return _process_quantity_entry_config(
            entry=self.model.factor_k_minor_axis,
            print_config=config_dict.factor_k
        )

    @cached_property
    def unbraced_length(self):
        return _process_quantity_entry_config(
            entry=self.model.unbraced_length_major_axis,
            print_config=config_dict.unbraced_length
        )

    @cached_property
    def minor_axis_slenderness(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.minor_axis_slenderness),
            print_config=config_dict.minor_axis_slenderness
        )

    @cached_property
    def slenderness_limit(self):
        return _process_quantity_entry_config(
            entry=Quantity(self.model.member_slenderness_limit),
            print_config=config_dict.slenderness_limit
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
            entry=self.model.elastic_flexural_buckling_stress_minor_axis,
            print_config=config_dict.elastic_buckling_critical_stress
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
            entry=self.model.flexural_buckling_critical_stress_minor_axis,
            print_config=config_dict.critical_stress
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
    def critical_stress(self):
        return _process_quantity_entry_config(
            entry=self.model.flexural_buckling_critical_stress_minor_axis,
            print_config=config_dict.critical_stress
        )

    @cached_property
    def critical_stress_equation(self):
        return self.non_slender_critical_stress

    @cached_property
    def strength_flexural_buckling(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_flexural_buckling,
            print_config=config_dict.strength_force
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
            print_config=config_dict.strength_force
        )

    @cached_property
    def design_strength_equation(self):
        return _design_strength(
            nominal_strength=self.nominal_strength,
            safety_factor=str(self.model.safety_factor.value),
            design_strength=self.design_strength,
            safety_factor_type=self.model.safety_factor,
            strength_type="force"
        )

    def resume(self):
        self.model.profile.latex.slenderness.axial_compression.resume()
        save_single_entry(
            content=self.minor_axis_slenderness_equation,
            file_name="member_minor_axis_slenderness.tex"
        )
        save_single_entry(
            content=self.elastic_buckling_critical_stress_equation,
            file_name="elastic_buckling_critical_stress.tex",
        )
        save_single_entry(
            content=self.critical_stress_equation,
            file_name="comp_critical_stress.tex"
        )
        save_single_entry(
            content=self.nominal_strength_equation,
            file_name="comp_nominal_strength.tex"
        )
        save_single_entry(
            content=self.design_strength_equation,
            file_name="comp_design_strength.tex"
        )

    @cached_property
    def resume_latex(self):
        slenderness = self.model.profile.latex.slenderness.axial_compression.resume_latex
        nominal_critical_strength = NoEscape(standard_wrapper(r"P_n = F_{cr} A_g"))
        nominal_critical_strength_terms = NoEscape(env.get_template("carga_critica_compressao_termos.tex").render())
        critical_stress_formulation = NoEscape(env.get_template("comp_critical_stress_formulation.tex").render())
        slenderness_beam = NoEscape(self.minor_axis_slenderness_equation),
        critical_stress = Subsubsection(
            title=NoEscape(r"Tens\~ao crit\'ica"),
            data=[
                NoEscape(self.elastic_buckling_critical_stress_equation),
                NoEscape(self.critical_stress_equation),
            ]
        )
        design_strength = Subsubsection(
            title=NoEscape(r"Carga cr\'itica de projeto"),
            data=[
                NoEscape(self.nominal_strength_equation),
                NoEscape(self.design_strength_equation),
            ]
        )
        calculation = Subsection(
            title=NoEscape(r"Carga cr\'itica"),
            data=[
                nominal_critical_strength,
                nominal_critical_strength_terms,
                critical_stress_formulation,
                NoEscape(self.minor_axis_slenderness_equation),
                NoEscape(self.elastic_buckling_critical_stress_equation),
                NoEscape(self.critical_stress_equation),
                NoEscape(self.nominal_strength_equation),
                NoEscape(self.design_strength_equation),
            ]
        )
        return Section(
            title=NoEscape(r"Compress\~ao axial"),
            data=[
                slenderness,
                calculation
            ]
        )


@dataclass
class BeamFlexureDoublySymmetricLatex:
    model: "BeamFlexureDoublySymmetric"

    @cached_property
    def major_axis(self):
        return BeamFlexureMajorAxisDoublySymmetricLatex(self.model)

    @cached_property
    def minor_axis(self):
        return BeamFlexureMinorAxisDoublySymmetricLatex(self.model)

    def resume(self):
        self.major_axis.resume()
        self.minor_axis.resume()

    # @cached_property
    # def resume_latex(self):
    #     return


@dataclass
class BeamFlexureMajorAxisDoublySymmetricLatex:
    model: "BeamFlexureDoublySymmetric"
    config_dict: ReportConfig = ReportConfig()

    def resume(self):
        self.model.profile.latex.slenderness.flexural_major_axis.resume()
        save_single_entry(
            content=self.yield_strength_equation,
            file_name="flex_major_axis_yield_strength.tex"
        )
        save_single_entry(
            content=self.model.profile.latex.limit_length_flexural_yield_equation,
            file_name="limit_lenght_flex_yidel.tex"
        )
        save_single_entry(
            content=self.model.profile.latex.effective_radius_of_gyration_equation,
            file_name="effective_radius_of_gyration.tex"
        )
        save_single_entry(
            content=Multline(
                data=NoEscape(self.model.profile.latex.limit_length_flexural_lateral_torsional_buckling_equation)
            ).dumps(),
            file_name="limit_length_flex_lateral_torsional_buck.tex"
        )
        save_single_entry(
            content=self.design_strength,
            file_name="flex_design_strengths.tex"
        )

    @cached_property
    def resume_latex(self):
        slenderness = self.model.profile.latex.slenderness.flexural_major_axis.resume_latex
        yield_strength = Subsubsection(
            title="Escoamento",
            data=NoEscape(self.yield_strength_equation),
        )
        lateral_torsional_formulation = NoEscape(
            env.get_template("flex_lateral_torsional_strength_formulation.tex").render()
        )
        limit_length_lateral_torsional_buckling_formulation = NoEscape(
            env.get_template("limit_length_lateral_torsional_buckling_formulation.tex").render()
        )
        lateral_torsional_buck = Subsubsection(
            title="Flambagem Lateral Torsional",
            data=[
                lateral_torsional_formulation,
                NoEscape(self.model.profile.latex.limit_length_flexural_yield_equation),
                limit_length_lateral_torsional_buckling_formulation,
                NoEscape(self.model.profile.latex.effective_radius_of_gyration_equation),
                NoEscape(self.model.profile.latex.limit_length_flexural_lateral_torsional_buckling_equation),
                NoEscape(self.model.latex.major_axis.lateral_torsional_buckling_strength_equation)
            ]
        )
        calculation = Subsection(
            title=NoEscape(r"Carga cr\'itica"),
            data=insert_between(
                [
                    yield_strength,
                    lateral_torsional_buck,
                    NoEscape(self.design_strength_equation),
                ]
            )
        )
        return Section(
            title=NoEscape(r"Flex\~ao eixo principal"),
            data=[
                slenderness,
                calculation
            ]
        )

    @cached_property
    def required_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.required_major_axis_flexural_strength,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def yield_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_major_axis_yield,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def yield_strength_equation(self):
        return _flexural_yield_nominal_strength(
            yield_stress=self.model.profile.material.latex.yield_stress,
            plastic_section_modulus=self.model.profile.area_properties.latex.major_axis_plastic_section_modulus,
            nominal_strength=self.yield_strength,
            axis="major"
        )

    @cached_property
    def mod_factor(self):
        return _process_quantity_entry_config(
            entry=self.model.lateral_torsional_buckling_modification_factor,
            print_config=config_dict.mod_factor
        )

    @cached_property
    def unbraced_length(self):
        return _process_quantity_entry_config(
            entry=self.model.unbraced_length_major_axis,
            print_config=config_dict.unbraced_length
        )

    @cached_property
    def lateral_torsional_buckling_strength_case_b(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_lateral_torsion_compact_case_b,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def lateral_torsional_buckling_strength_case_b_equation(self):
        return _flexural_lateral_torsional_buckling_strength_case_b(
            mod_factor=self.mod_factor,
            yield_stress=self.model.profile.material.latex.yield_stress,
            plastic_moment=self.yield_strength,
            elastic_major_axis_section_modulus=self.model.profile.area_properties.latex
                .major_axis_elastic_section_modulus,
            unbraced_length=self.unbraced_length,
            limit_length_yield=self.model.profile.latex.limit_length_flexural_yield,
            limit_length_lateral_torsional_buckling=self.model.profile.latex
                .limit_length_flexural_lateral_torsional_buckling,
            nominal_strength=self.lateral_torsional_buckling_strength_case_b
        )

    @cached_property
    def lateral_torsional_buckling_strength_equation(self) -> str | None:
        # TODO implement case c and check which case is appropriate
        return _flexural_lateral_torsional_buckling_strength(
            case_b=self.lateral_torsional_buckling_strength_case_b_equation,
            case_c="Case c: Not Implemented",
            length_between_braces=self.model.unbraced_length_major_axis,
            limiting_length_yield=self.model.profile.limit_length_yield,
            limiting_length_torsional_buckling=self.model.profile.limit_length_torsional_buckling
        )

    @cached_property
    def nominal_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.nominal_strength_major_axis,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def design_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.design_strength_major_axis,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def design_strength_equation(self):
        return _design_strength(
            nominal_strength=self.nominal_strength,
            safety_factor_type=self.model.safety_factor,
            safety_factor=str(self.model.safety_factor.value),
            design_strength=self.design_strength,
            strength_type="moment"
        )


@dataclass
class BeamFlexureMinorAxisDoublySymmetricLatex:
    model: "BeamFlexureDoublySymmetric"

    def resume(self):
        self.model.profile.latex.slenderness.flexural_minor_axis.resume()
        save_single_entry(
            content=self.yield_strength_equation,
            file_name="flex_minor_axis_yield_strength.tex"
        )
        save_single_entry(
            content=self.design_strength_equation,
            file_name="flex_minor_axis_design_strength.tex"
        )

    @cached_property
    def resume_latex(self):
        slenderness = self.model.profile.latex.slenderness.flexural_minor_axis.resume_latex
        calculation = Subsection(
            title=NoEscape(r"Carga cr\'itica"),
            data=insert_between(
                [
                    NoEscape(self.yield_strength_equation),
                    NoEscape(self.design_strength_equation),
                ]
            )
        )
        return Section(
            title=NoEscape(r"Flex\~ao eixo secund\'ario"),
            data=insert_between(
                [
                    slenderness,
                    calculation
                ]
            )
        )

    @cached_property
    def required_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.required_minor_axis_flexural_strength,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def yield_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.strength_minor_axis_yield,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def yield_strength_equation(self):
        return _flexural_yield_nominal_strength(
            yield_stress=self.model.profile.material.latex.yield_stress,
            plastic_section_modulus=self.model.profile.area_properties.latex.minor_axis_plastic_section_modulus,
            nominal_strength=self.yield_strength,
            axis="minor"
        )

    @cached_property
    def nominal_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.nominal_strength_minor_axis,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def design_strength(self):
        return _process_quantity_entry_config(
            entry=self.model.design_strength_minor_axis,
            print_config=config_dict.strength_moment
        )

    @cached_property
    def design_strength_equation(self):
        return _design_strength(
            nominal_strength=self.nominal_strength,
            safety_factor_type=self.model.safety_factor,
            safety_factor=str(self.model.safety_factor.value),
            design_strength=self.design_strength,
            strength_type="moment"
        )


@dataclass
class BeamCompressionFlexureDoublySymmetricEffectiveLengthLatex:
    model: "BeamCompressionFlexureDoublySymmetricEffectiveLength"

    @cached_property
    def data_table(self):
        return _dataframe_table_columns(
            df=self.model.data_table_df,
            unit_display="cell",
            include_description=True
        ).dumps()

    @cached_property
    def data_table_latex(self):
        return _dataframe_table_columns(
            df=self.model.data_table_df,
            unit_display="cell",
            include_description=True
        )

    def resume(self):
        self.model.profile.material.latex.resume()
        self.model.profile.latex.resume()
        save_single_entry(
            content=self.data_table,
            file_name="beam_param.tex"
        )
        self.model.compression.latex.resume()
        self.model.flexure.latex.resume()

    @cached_property
    def resume_latex(self):
        material = self.model.profile.material.latex.resume_latex
        profile = self.model.profile.latex.resume_latex
        beam_data = Section(
            title="Viga",
            data=self.data_table_latex
        )
        compression = self.model.compression.latex.resume_latex
        flexure_major = self.model.flexure.latex.major_axis.resume_latex
        flexure_minor = self.model.flexure.latex.minor_axis.resume_latex
        sections = insert_between(
            [
                material.dumps(),
                profile.dumps(),
                beam_data.dumps(),
                compression.dumps(),
                flexure_major.dumps(),
                flexure_minor.dumps()
            ]
        )
        doc_str = "".join(sections)
        doc = _build_doc(doc_str)
        return doc

    @cached_property
    def critical_loads_report(self):
        title = r"\section{Cargas cr\'iticas}"
        material = self.model.profile.material.latex.data_table
        title_material = r"\section{Material}"
        profile_properties = self.model.profile.latex.data_table
        slenderness_tile = r"\subsection{Slenderness ratio}"
        flange_slenderness_title = r"\subsubsection{Flange}"
        flange_slenderness = self.model.profile.latex.slenderness.flange_slenderness_equation
        web_slenderness_title = r"\subsubsection{Web}"
        web_slendernses = self.model.profile.latex.slenderness.web_slenderness_equation
        title_profile = r"\section{Propriedades da Se\c{c}\~ao}"
        compression = self.model.compression.latex.resume
        flexure_major_axis = self.model.flexure.latex.major_axis.resume
        flexure_minor_axis = self.model.flexure.latex.minor_axis.resume
        title_combined_criteria = r"\section{Crit\'erio combinado}"
        beam = self.data_table
        title_beam = r"\section{Dados da viga e cargas aplicadas}"
        title_profile_slenderness = r"\subsection{Raz\~oes de esbeltez}"
        flange_slenderness_ratio = self.model.profile.latex.slenderness.flange_slenderness_equation
        web_slenderness_ratio = self.model.profile.latex.slenderness.web_slenderness_equation
        string = CONCATENATE_STRING
        document_string = string.join(
            (
                title_material,
                material,
                title_profile,
                profile_properties,
                title_profile_slenderness,
                flange_slenderness_ratio,
                web_slenderness_ratio,
                title_beam,
                beam,
                compression,
                flexure_major_axis,
                flexure_minor_axis,
                title_combined_criteria,
                self.model.compression.latex.axial_strength_ratio_equation,
                self.flexure_compression_h1_criteria_equation
            )
        )
        return _build_doc(document_string)

    @cached_property
    def flexure_compression_h1_criteria(self):
        return _process_quantity_entry_config(
            entry=self.model.compression_flexure_combined_criteria_h1_1,
            print_config=config_dict.criteria
        )

    @cached_property
    def flexure_compression_h1_criteria_equation(self):
        if self.model.compression.axial_strength_ratio < 0.2:
            axial_strength_ratio = "lower_than_0_2"
        else:
            axial_strength_ratio = "greater_than_0_2"
        return _flexure_compression_h1_criteria_equation(
            axial_strength_ratio=axial_strength_ratio,
            required_axial_strength=self.model.compression.latex.required_strength,
            design_axial_strength=self.model.compression.latex.design_strength,
            required_flexural_major_axis_strength=self.model.flexure.latex.major_axis.required_strength,
            design_strength_flexural_major_axis=self.model.flexure.latex.major_axis.design_strength,
            required_flexural_minor_axis_strength=self.model.flexure.latex.minor_axis.required_strength,
            design_strength_flexural_minor_axis=self.model.flexure.latex.minor_axis.design_strength,
            criteria=self.flexure_compression_h1_criteria
        )
