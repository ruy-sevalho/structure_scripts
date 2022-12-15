from functools import partial
from typing import Collection, Literal

from pandas import DataFrame, concat, Series

from structure_scripts.ansys import (
    BEAM_RESULTS,
    BEAM,
    FX,
    MY,
    MZ,
    FXI,
    FXJ,
    MYI,
    MYJ,
    MZJ,
    MZI,
)


def add_load_case(
    df: DataFrame, load_case: Collection[tuple[str, float]], name: str
):
    for result in BEAM_RESULTS:
        exp = " + ".join(
            [f"{result}_{case} * {factor}" for case, factor in load_case]
        )
        df[f"{result}_{name}"] = df.eval(exp)
    return df


def add_load_cases(
    df: DataFrame,
    load_cases: Collection[tuple[str, Collection[tuple[str, float]]]],
):
    for load_case in load_cases:
        df = concat(
            (df, add_load_case(df, load_case=load_case[1], name=load_case[0]))
        )
    return df


# def check_load_case_combined_compression_and_flexure(
#         df: DataFrame, load_case: str
# ):


def _h1_comp_flex_check(
    comp_load: float,
    flex_major_load: float,
    flex_minor_load: float,
    comp_str: float,
    flex_major_str: float,
    flex_minor_str: float,
):
    comp_ratio = comp_load / comp_str
    moment_ratio = (
        flex_major_load / flex_major_str + flex_minor_load / flex_minor_str
    )
    if comp_ratio < 0.2:
        return comp_ratio / 2 + moment_ratio
    else:
        return comp_ratio + 8 / 9 * moment_ratio


def _row_check_load_case_combined_compression_and_flexure(
    row: Series,
    case_name: str,
    elem_node: Literal["i", "j"],
    beams_strengths: dict[str, dict[str, float]],
):
    beam_str = beams_strengths[row[BEAM]]
    comp_str = beam_str[FX]
    flex_major_str = beam_str[MY]
    flex_minor_str = beam_str[MZ]
    comp_load = abs(row[f"{FX}{elem_node}_{case_name}"])
    flex_major_load = abs(row[f"{MY}{elem_node}_{case_name}"])
    flex_minor_load = abs(row[f"{MZ}{elem_node}_{case_name}"])
    comp_ratio = comp_load / comp_str
    moment_ratio = (
        flex_major_load / flex_major_str + flex_minor_load / flex_minor_str
    )
    if comp_ratio < 0.2:
        return comp_ratio / 2 + moment_ratio
    else:
        return comp_ratio + 8 / 9 * moment_ratio


def check_load_case_combined_compression_and_flexure(
    df: DataFrame,
    case_name: str,
    beams_strengths: dict[str, dict[str, float]],
):
    for node in ("i", "j"):
        func = partial(
            _row_check_load_case_combined_compression_and_flexure,
            case_name=case_name,
            elem_node=node,
            beams_strengths=beams_strengths,
        )
        df[f"h1_criteria_{node}_{case_name}"] = df.apply(func, axis=1)
    return df
