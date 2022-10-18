import pathlib
from datetime import datetime
from enum import Enum
from itertools import chain
from typing import Literal, Optional, Union, Callable, Collection, Any
from functools import partial

import pandas as pd
from jinja2 import PackageLoader
from jinja2 import Environment as JinjaEnvironment
from pylatex import (
    NoEscape,
    Table,
    Tabular
)
from pylatex import Quantity as LatexQuantity
from pylatex.base_classes import Environment, CommandBase, Command
from pylatex.utils import dumps_list
from quantities import Quantity, percent

from structure_scripts.aisc_360_10.criteria import AllowableStrengthDesign, LoadAndResistanceFactorDesign, SafetyFactor
from structure_scripts.shared.report_config import ReportConfig, PrintOptions
from structure_scripts.aisc_360_10.section_slenderness import Slenderness

env = JinjaEnvironment(loader=PackageLoader("structure_scripts.aisc_360_10"))

CONCATENATE_STRING = env.get_template("concatenation.tex").render()


class Center(Environment):
    pass


class Landscape(Environment):
    pass


class TableOfContents(CommandBase):
    pass


class ListOfTables(CommandBase):
    pass


class Alpha(CommandBase):
    pass


class Lambda(CommandBase):
    pass


class Frac(CommandBase):
    pass


class Sqrt(CommandBase):
    pass


class Multline(Environment):
    pass


class Split(Environment):
    pass


class Equation(Environment):
    pass


alpha = Alpha()
lambda_ = Lambda()
axis_index_table = {
    "major": "x",
    "minor": "y"
}


class Tblr(Tabular):
    """Blank copy of Tabular class from pylatex, but with tblr tables, from tabularray package."""


def _wrapper(start: str, content: str, end: str):
    return env.get_template("wrapper.tex").render(start=start, content=content, end=end)


def _inline_math(content: str):
    return _wrapper(start=r"$", content=content, end=r"$")


def standard_wrapper(content: str):
    return _wrapper(start=r"\[", content=content, end=r"\]")


def inline_math_dec(func):
    def inner(*args, **kwargs):
        return standard_wrapper(func(*args, **kwargs))

    return inner


def multline(content: str):
    return _wrapper(
        start=r"\begin{multline*}",
        content=content,
        end=r"\end{multline*}"
    )


def _get_header(
        label: Union[str, NoEscape],
        units: Optional[str] = None,
        unit_display: Literal["header", "cell"] = "header",
) -> Union[str, NoEscape]:
    if unit_display == "header" and not units == percent:  # or units == criteria:
        units_string = LatexQuantity(Quantity(1, units)).dumps()
        units_string = units_string[:4] + units_string[5:]
        header = ["{", label, r"\\ ", units_string, "}"]
        header = dumps_list(header, escape=False, token="")
    else:
        header = label
    return header


def _process_quantity_entry(
        entry: Quantity,
        convert_units: Optional[str] = None,
        round_precision: int = 2,
        unit_display: Literal["header", "cell"] = "header",
):
    if pd.isna(entry):
        return "-"
    if convert_units is not None:
        entry = entry.rescale(convert_units)
    if unit_display == "header" and not entry.units == percent:
        entry = entry.magnitude
    return LatexQuantity(entry, options={"round-precision": round_precision})


def _process_quantity_entry_to_string(
        entry: Quantity,
        convert_units: Optional[str] = None,
        round_precision: int = 2,
        unit_display: Literal["header", "cell"] = "header",
):
    if pd.isna(entry):
        return "-"
    if convert_units is not None:
        entry = entry.rescale(convert_units)
    if unit_display == "header" and not entry.units == percent:
        entry = entry.magnitude
    return LatexQuantity(entry, options={"round-precision": round_precision}).dumps()


def _process_entry(
        entry: Quantity | int | float | str,  # Criteria
        convert_units: Optional[str],
        round_precision: int = 2,
        unit_display: Literal["header", "cell"] = "header",
):
    process_quantity = partial(
        _process_quantity_entry,
        convert_units=convert_units,
        round_precision=round_precision,
        unit_display=unit_display,
    )
    # process_criteria = lambda x: x.to_latex(round_precision=round_precision)
    process_nan = lambda x: "-"
    process_others = lambda x: x
    process_enum = lambda x: x.value
    if isinstance(entry, Quantity):
        process_function = process_quantity
    # elif isinstance(entry, Criteria):
    #     process_function = process_criteria
    elif pd.isna(entry):
        process_function = process_nan
    elif isinstance(entry, Enum):
        process_function = process_enum
    else:
        process_function = process_others
    return process_function(entry)


def _process_column_2(
        column: pd.Series,
        convert_units: Optional[str],
        round_precision: int = 2,
        unit_display: Literal["header", "cell"] = "header",
):
    return [
        _process_entry(
            row,
            convert_units=convert_units,
            round_precision=round_precision,
            unit_display=unit_display,
        )
        for row in column
    ]


def _dataframe_table_columns(
        df: pd.DataFrame,
        config_dict: dict[
            str, PrintOptions
        ] = ReportConfig().to_dict(),  # learn to use bloody config
        unit_display: Literal["header", "cell"] = "header",
        include_description: bool = False
) -> Tblr:
    width_correction = 2 if include_description else 1
    width = df.shape[0] + width_correction
    # column specifications of tabularray package for calculation_memory
    first_row = "Q[l, m]"
    remaining_rows = " Q[c, m]"
    table_spec = f"{first_row}{(width - 1) * remaining_rows}"
    tblr = Tblr(table_spec=table_spec, width=width)
    header_list = []
    table = [[] for _ in range(df.shape[1])]
    columns = df.columns
    # for row, name in enumerate(df.columns):
    #     print(f"row: {row}")
    #     print(f"name: {name}")
    for row, name in enumerate(df.columns):
        print_config = config_dict.get(name, PrintOptions())
        if include_description:
            description = print_config.description or name.replace("_", " ")
            table[row].append(description)
        # in calculation_memory _ is a special character
        label = print_config.label or name.replace("_", " ")
        # Assuming dataframe has at least one row and all objects
        # in a given column are of the same type or nan.
        # Dropping nan in the series and getting the first element
        # to determine what type the column is populated
        instance = df[name].dropna().head(1).reset_index(drop=True).at[0]

        if isinstance(instance, Quantity):
            units = print_config.print_units or instance.units
            header = _get_header(label=label, units=units, unit_display=unit_display)
        else:
            header = label
        column = _process_column_2(
            df[name],
            convert_units=print_config.print_units,
            round_precision=print_config.round_precision,
            unit_display=unit_display,
        )
        table[row].append(header)

        # table[row].append(column[0])
        # continue
        for item in column:
            # print(f"row: {row}")
            # print(f"name: {name}")
            table[row].append(item)
    for row in table:
        tblr.add_row(row)
    return tblr


def _dataframe_table_rows(
        df: pd.DataFrame,
        config_dict: dict[
            str, PrintOptions
        ] = ReportConfig().to_dict(),  # learn to use bloody config
        unit_display: Literal["header", "cell"] = "header",
) -> Tblr:
    width = df.shape[1]
    # column specifications of tabularray package for calculation_memory
    first_row = "Q[l, m]"
    remaining_rows = " Q[c, m]"
    table_spec = f"{first_row}{(width - 1) * remaining_rows}"
    tblr = Tblr(table_spec=table_spec, width=width)
    header_list = []
    table = [[] for _ in range(df.shape[0])]
    for name in df.columns:
        print_config = config_dict.get(name, PrintOptions())
        # in calculation_memory _ is a special character
        label = print_config.label or name.replace("_", " ")
        # Assuming dataframe has at least one row and all objects
        # in a given column are of the same type or nan.
        # Dropping nan in the series and getting the first element
        # to determine what type the column is populated
        instance = df[name].dropna().head(1).reset_index(drop=True).at[0]

        if isinstance(instance, Quantity):
            units = print_config.print_units or instance.units
            header = _get_header(label=label, units=units, unit_display=unit_display)
        else:
            header = label
        column = _process_column_2(
            df[name],
            convert_units=print_config.print_units,
            round_precision=print_config.round_precision,
            unit_display=unit_display,
        )
        for row, table_row in zip(column, table):
            table_row.append(row)
        header_list.append(header)
    tblr.add_row(header_list)
    tblr.append(Command("midrule"))
    for row in table:
        tblr.add_row(row)
    return tblr


def _add_df_table(
        df: pd.DataFrame,
        caption: str,
        config_dict: dict[str, PrintOptions] = ReportConfig().to_dict(),
):
    table = Table(position="H")
    table.add_caption(caption)
    tblr = Center()
    tblr.append(
        _dataframe_table_rows(df=df, config_dict=config_dict, unit_display="header")
    )
    table.append(tblr)
    return table


def _add_df_table_transposed(
        df: pd.DataFrame,
        caption: str,
        config_dict: dict[str, PrintOptions] = ReportConfig().to_dict(),
):
    table = Table(position="H")
    table.add_caption(caption)
    tblr = Center()
    tblr.append(
        _dataframe_table_rows(df=df, config_dict=config_dict, unit_display="header")
    )
    table.append(tblr)
    return table


def _process_quantity_entry_config(entry, print_config: PrintOptions):
    if isinstance(entry, float | int):
        entry = Quantity(entry)
    return _process_quantity_entry_to_string(
        entry=entry,
        round_precision=print_config.round_precision,
        convert_units=print_config.print_units,
        unit_display="cell"
    )


def _slenderness_default_limit_ratio_latex(
        factor: str,
        modulus: str,
        yield_stress: str,
        limit_ratio: str,
        limit_ratio_type: Literal["slender", "compact"],
        wrapper: Callable[[str], str] = standard_wrapper,
):
    table = {
        "slender": "r",
        "compact": "p"
    }
    slenderness_type_subscript = table[limit_ratio_type]
    template = env.get_template("slenderness_default_limit_ratio.tex")
    return wrapper(
        template.render(
            factor=factor,
            modulus=modulus,
            yield_stress=yield_stress,
            limit_ratio=limit_ratio,
            slenderness_type=slenderness_type_subscript
        )
    )


def _member_slenderness_minor_axis_flexural_bucking_latex(
        factor_k: str,
        length: str,
        radius_of_gyration: str,
        slenderness_value: str,
        modulus: str,
        yield_stress: str,
        slenderness_limit: str,
        inequality_sign: Literal[r"\leq", ">"],
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("member_minor_axis_flexural_buckling_slenderness.tex")
    return wrapper(
        template.render(
            factor_k=factor_k,
            length=length,
            radius_of_gyration=radius_of_gyration,
            slenderness_value=slenderness_value,
            inequality_sign=inequality_sign,
            modulus=modulus,
            yield_stress=yield_stress,
            slenderness_limit=slenderness_limit
        )
    )


def _elastic_buckling_critical_stress_latex(
        modulus: str,
        length: str,
        factor_k: str,
        radius_of_gyration: str,
        elastic_buckling_critical_stress: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("elastic_buckling_critical_stress.tex")
    return wrapper(
        template.render(
            modulus=modulus,
            length=length,
            factor_k=factor_k,
            radius_of_gyration=radius_of_gyration,
            elastic_buckling_critical_stress=elastic_buckling_critical_stress
        )
    )


def _axial_compression_non_slender_critical_stress_lower_than(
        yield_stress: str,
        elastic_buckling_critical_stress: str,
        critical_stress: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("axial_compression_critical_stress_lower_than.tex")
    return wrapper(
        template.render(
            yield_stress=yield_stress,
            elastic_buckling_critical_stress=elastic_buckling_critical_stress,
            critical_stress=critical_stress
        )
    )


def _axial_compression_non_slender_critical_stress_greater_than(
        yield_stress: str,
        elastic_buckling_critical_stress: str,
        critical_stress: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("axial_compression_critical_stress_greater_than.tex")
    return wrapper(
        template.render(
            yield_stress=yield_stress,
            elastic_buckling_critical_stress=elastic_buckling_critical_stress,
            critical_stress=critical_stress
        )
    )


def _axial_compression_nominal_strength(
        critical_stress: str,
        area: str,
        nominal_strength: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    table = {"force": "P", "moment": "m"}
    template = env.get_template("nominal_strength_force.tex")
    return wrapper(
        template.render(
            critical_stress=critical_stress,
            area=area,
            nominal_strength=nominal_strength,
        )
    )


TABLE_STRENGTH_STRINGS = {"force": "P", "moment": "M"}


def _design_strength_asd(
        nominal_strength: str,
        safety_factor: str,
        design_strength: str,
        strength_type: Literal["force", "moment"],
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("design_strength_asd.tex")
    return wrapper(
        template.render(
            nominal_strength=nominal_strength,
            safety_factor=safety_factor,
            design_strength=design_strength,
            strength_type=TABLE_STRENGTH_STRINGS[strength_type]
        )
    )


def _design_strength_lfrd(
        nominal_strength: str,
        safety_factor: str,
        design_strength: str,
        strength_type: Literal["force", "moment"],
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("design_strength_lfrd.tex")
    return wrapper(
        template.render(
            nominal_strength=nominal_strength,
            safety_factor=safety_factor,
            design_strength=design_strength,
            strength_type=TABLE_STRENGTH_STRINGS[strength_type]
        )
    )


def _design_strength(
        nominal_strength: str,
        safety_factor: str,
        design_strength: str,
        safety_factor_type: SafetyFactor,
        strength_type: Literal["force", "moment"],
        wrapper: Callable[[str], str] = standard_wrapper,
):
    table = {
        AllowableStrengthDesign: _design_strength_asd,
        LoadAndResistanceFactorDesign: _design_strength_lfrd
    }
    return table[type(safety_factor_type)](
        nominal_strength=nominal_strength,
        safety_factor=safety_factor,
        design_strength=design_strength,
        strength_type=strength_type,
        wrapper=wrapper
    )


def _flexural_yield_nominal_strength(
        yield_stress: str,
        plastic_section_modulus: str,
        nominal_strength: str,
        axis: Literal["major", "minor"],
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("flexural_yield_nominal_strength.tex")
    return wrapper(
        template.render(
            yield_stress=yield_stress,
            plastic_section_modulus=plastic_section_modulus,
            nominal_strength=nominal_strength,
            axis_index=axis_index_table[axis]
        )
    )


def _limit_length_yield(
        minor_axis_radius_of_gyration: str,
        modulus_linear: str,
        yield_stress: str,
        limit_length: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    template = env.get_template("limit_length_yield.tex")
    return wrapper(
        template.render(
            minor_axis_radius_of_gyration=minor_axis_radius_of_gyration,
            modulus_linear=modulus_linear,
            yield_stress=yield_stress,
            limit_length=limit_length
        )
    )


def _limit_length_lateral_torsional_buckling(
        effective_radius_of_gyration: str,
        modulus_linear: str,
        yield_stress: str,
        elastic_major_axis_section_modulus: str,
        torsional_constant: str,
        coefficient_c: str,
        distance_between_centroids: str,
        limit_length: str,
        wrapper: Callable[[str], str] = multline,
):
    template = env.get_template("limit_length_lateral_torsional_buckling.tex")
    return wrapper(
        template.render(
            effective_radius_of_gyration=effective_radius_of_gyration,
            modulus_linear=modulus_linear,
            yield_stress=yield_stress,
            elastic_major_axis_section_modulus=elastic_major_axis_section_modulus,
            torsional_constant=torsional_constant,
            coefficient_c=coefficient_c,
            distance_between_centroids=distance_between_centroids,
            limit_length=limit_length
        )
    )


def _effective_radius_of_gyration_equation(
        minor_axis_inertia: str,
        warping_constant: str,
        major_axis_section_modulus: str,
        effective_radius_of_gyration: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    return wrapper(
        env.get_template("effective_radius_of_gyration.tex").render(
            minor_axis_inertia=minor_axis_inertia,
            warping_constant=warping_constant,
            major_axis_section_modulus=major_axis_section_modulus,
            effective_radius_of_gyration=effective_radius_of_gyration,
        )
    )


def _flexural_lateral_torsional_buckling_strength_case_b(
        mod_factor: str,
        plastic_moment: str,
        yield_stress: str,
        elastic_major_axis_section_modulus: str,
        unbraced_length: str,
        limit_length_yield: str,
        limit_length_lateral_torsional_buckling: str,
        nominal_strength: str,
        wrapper: Callable[[str], str] = multline,
):
    template = env.get_template("flexural_lateral_torsional_buckling_strength_case_b.tex")
    return wrapper(
        template.render(
            mod_factor=mod_factor,
            plastic_moment=plastic_moment,
            yield_stress=yield_stress,
            elastic_major_axis_section_modulus=elastic_major_axis_section_modulus,
            unbraced_length=unbraced_length,
            limit_length_yield=limit_length_yield,
            limit_length_lateral_torsional_buckling=limit_length_lateral_torsional_buckling,
            nominal_strength=nominal_strength
        )
    )


def _build_doc(document: str, date: str = datetime.now()):
    template = env.get_template("document.tex")
    return template.render(
        body=document,
        date=date
    )


def _axial_strength_ratio_equation(
        required_strength: str,
        design_strength: str,
        ratio: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    return wrapper(
        env.get_template("axial_strength_ratio.tex").render(
            required_strength=required_strength,
            design_strength=design_strength,
            ratio=ratio
        )
    )


def _flexure_compression_h1_criteria_equation(
        axial_strength_ratio: Literal["lower_than_0_2", "greater_than_0_2"],
        required_axial_strength: str,
        design_axial_strength: str,
        required_flexural_major_axis_strength: str,
        design_strength_flexural_major_axis: str,
        required_flexural_minor_axis_strength: str,
        design_strength_flexural_minor_axis: str,
        criteria: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    force_factor = {
        "lower_than_0_2": r"2 \cdot",
        "greater_than_0_2": ""
    }
    moment_factor = {
        "lower_than_0_2": "",
        "greater_than_0_2": r"\frac{8}{9}"
    }
    return wrapper(
        env.get_template("flexure_compression_h1_criteria.tex").render(
            force_factor=force_factor[axial_strength_ratio],
            moment_factor=moment_factor[axial_strength_ratio],
            required_axial_strength=required_axial_strength,
            required_flexural_major_axis_strength=required_flexural_major_axis_strength,
            required_flexural_minor_axis_strength=required_flexural_minor_axis_strength,
            design_axial_strength=design_axial_strength,
            design_strength_flexural_major_axis=design_strength_flexural_major_axis,
            design_strength_flexural_minor_axis=design_strength_flexural_minor_axis,
            criteria=criteria
        )
    )


def _ratio_equation(
        numerator_symbol: str,
        numerator_value: str,
        denominator_symbol: str,
        denominator_value: str,
        ratio_value: str,
        ratio_symbol: str,
        wrapper: Callable[[str], str] = standard_wrapper,
):
    return wrapper(
        env.get_template("ratio.tex").render(
            numerator_value=numerator_value,
            numerator_symbol=numerator_symbol,
            denominator_symbol=denominator_symbol,
            denominator_value=denominator_value,
            ratio_value=ratio_value,
            ratio_symbol=ratio_symbol
        )
    )


TABLE_ELEMENT = {
        "flange": ("flange", "f"),
        "web": ("alma", "w")
    }


def _axial_slenderness_result(
        slenderness: Slenderness,
        element: str,
) -> str:
    table_slenderness = {
        Slenderness.SLENDER: (">", "esbelta"),
        Slenderness.NON_SLENDER: ("<", NoEscape(r"n\~ao esbelta")),
    }
    inequality_sign, slenderness_type = table_slenderness[slenderness]
    element_name, element_abbreviation = TABLE_ELEMENT[element]
    return env.get_template("compression_slenderness_result.tex").render(
        inequality_sign=inequality_sign,
        slenderness_type=slenderness_type,
        element_name=element_name,
        element_abbreviation=element_abbreviation
    )


def _flexural_slenderness_result(
        slenderness:Slenderness,
        element: str
):
    table_slenderness = {
        Slenderness.SLENDER: "flexural_slenderness_result_slender.tex",
        Slenderness.NON_COMPACT: "flexural_slenderness_result_non_compact.tex",
        Slenderness.COMPACT: "flexural_slenderness_result_compact.tex"
    }
    element_name, element_abbreviation = TABLE_ELEMENT[element]
    return env.get_template(table_slenderness[slenderness]).render(
        element_name=element_name,
        element_abbreviation=element_abbreviation,
    )


def _build_single_element(content: str):
    template = env.get_template("single_element.tex")
    return template.render(
        content=content
    )


def save_single_entry(content: str, file_name: str):
    path = pathlib.Path(r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\pdf_maker\tex_files") / file_name
    content = _build_single_element(content)
    with open(path, "w") as f:
        f.write(content)


def insert_between(collection: Collection[Any], separator: str = "\n"):
    col = ((item, separator) for item in collection)
    return list(chain(*col))