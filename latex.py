from typing import Literal, Optional, Union
from functools import partial
import pandas as pd
from pylatex import (
    Document,
    MiniPage,
    NoEscape,
    Quantity,
    Section,
    Subsection,
    Subsubsection,
    Table,
    Tabular,
    Package,
    NewPage,
)
from pylatex.base_classes import Environment, CommandBase, Command
from pylatex.labelref import Label
from pylatex.math import Math
from pylatex.utils import dumps_list
import quantities as pq

from report_config import ReportConfig, PrintOptions


class Center(Environment):
    pass


class Landscape(Environment):
    pass


class TableOfContents(CommandBase):
    pass


class ListOfTables(CommandBase):
    pass


class Tblr(Tabular):
    """Blank copy of Tabular class from pylatex, but with tblr tables, from tabularray package."""


def _get_header(
        label: Union[str, NoEscape],
        units: Optional[str] = None,
        unit_display: Literal["header", "cell"] = "header",
) -> Union[str, NoEscape]:
    if unit_display == "header" and not units == pq.percent:  # or units == criteria:
        units_string = Quantity(pq.Quantity(1, units)).dumps()
        units_string = units_string[:4] + units_string[5:]
        header = ["{", label, r"\\ ", units_string, "}"]
        header = dumps_list(header, escape=False, token="")
    else:
        header = label
    return header


def _process_entry(
        entry: pq.Quantity | int | float | str,  # Criteria
        convert_units: Optional[str],
        round_precision: int = 2,
        unit_display: Literal["header", "cell"] = "header",
):
    def _process_quantity_entry(
            entry: pq.Quantity,
            convert_units: Optional[str] = None,
            round_precision: int = 2,
            unit_display: Literal["header", "cell"] = "header",
    ):
        if pd.isna(entry):
            return "-"
        if convert_units is not None:
            entry = entry.rescale(convert_units)
        if unit_display == "header" and not entry.units == pq.percent:
            entry = entry.magnitude
        return Quantity(entry, options={"round-precision": round_precision})

    process_quantity = partial(
        _process_quantity_entry,
        convert_units=convert_units,
        round_precision=round_precision,
        unit_display=unit_display,
    )
    # process_criteria = lambda x: x.to_latex(round_precision=round_precision)
    process_nan = lambda x: "-"
    process_others = lambda x: x
    if isinstance(entry, pq.Quantity):
        process_function = process_quantity
    # elif isinstance(entry, Criteria):
    #     process_function = process_criteria
    elif pd.isna(entry):
        process_function = process_nan
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
) -> Tblr:
    width = df.shape[0] + 1
    # column specifications of tabularray package for latex
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
        # in latex _ is a special character
        label = print_config.label or name.replace("_", " ")
        # Assuming dataframe has at least one row and all objects
        # in a given column are of the same type or nan.
        # Dropping nan in the series and getting the first element
        # to determine what type the column is populated
        instance = df[name].dropna().head(1).reset_index(drop=True).at[0]

        if isinstance(instance, pq.Quantity):
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
    # column specifications of tabularray package for latex
    first_row = "Q[l, m]"
    remaining_rows = " Q[c, m]"
    table_spec = f"{first_row}{(width - 1) * remaining_rows}"
    tblr = Tblr(table_spec=table_spec, width=width)
    header_list = []
    table = [[] for _ in range(df.shape[0])]
    for name in df.columns:
        print_config = config_dict.get(name, PrintOptions())
        # in latex _ is a special character
        label = print_config.label or name.replace("_", " ")
        # Assuming dataframe has at least one row and all objects
        # in a given column are of the same type or nan.
        # Dropping nan in the series and getting the first element
        # to determine what type the column is populated
        instance = df[name].dropna().head(1).reset_index(drop=True).at[0]

        if isinstance(instance, pq.Quantity):
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
