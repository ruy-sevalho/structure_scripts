from functools import partial
from typing import Collection, Literal

from pandas import DataFrame, Series

from structure_scripts.process_external_files.ansys import (
    BEAM_RESULTS,
    BEAM,
    FX,
    MY,
    MZ,
)


def _add_load_case(
    df: DataFrame,
    load_case: Collection[tuple[str, float]],
    name: str,
    results: Collection[str] = BEAM_RESULTS,
):
    for result in results:
        exp = " + ".join(
            [f"{result}_{case} * {factor}" for case, factor in load_case]
        )
        df[f"{result}_{name}"] = df.eval(exp)
    return df

def _add_multiindex_load_case(
    df: DataFrame,
    load_case: Collection[tuple[str, float]],
    name: str,
    results: Collection[str] = BEAM_RESULTS,
):



# def _add_load_cases(
#     df: DataFrame,
#     load_cases: Collection[tuple[str, Collection[tuple[str, float]]]],
# ):
#     for load_case in load_cases:
#
#         df = _add_load_case(df, load_case=load_case[1], name=load_case[0])
#     return df


def add_load_cases(
    base_results: DataFrame,
    load_cases: DataFrame,
    results: Collection[str] = BEAM_RESULTS,
):
    comb = "Comb"
    for index, load_case in load_cases.iterrows():
        lc = dict(load_case.to_dict())
        lc.pop(comb)
        lc = tuple((key, value) for key, value in lc.items())
        base_results = _add_load_case(
            base_results, load_case=lc, name=load_case[comb], results=results
        )
    return base_results


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


def _ratio(
    row: Series,
    case_name: str,
    elem_node: Literal["i", "j"],
    beams_strengths: dict[str, dict[str, float]],
    load_type: Literal[FX, MY, MZ],
):
    b = beams_strengths.get(row[BEAM], None)
    if not b:
        return None
    return abs(
        row[f"{load_type}{elem_node}_{case_name}"]
        / beams_strengths[row[BEAM]][load_type]
    )


def _row_check_load_case_combined_compression_and_flexure(
    row: Series,
    case_name: str,
    elem_node: Literal["i", "j"],
    beams_strengths: dict[str, dict[str, float]],
):

    beam_str = beams_strengths.get(row[BEAM], None)
    if not beam_str:
        return None
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
        for load in (FX, MY, MZ):
            func = partial(
                _ratio,
                case_name=case_name,
                elem_node=node,
                beams_strengths=beams_strengths,
                load_type=load,
            )
            df[f"{load}{node}_{case_name}_ratio"] = df.apply(func, axis=1)
        func = partial(
            _row_check_load_case_combined_compression_and_flexure,
            case_name=case_name,
            elem_node=node,
            beams_strengths=beams_strengths,
        )
        df[f"h1_criteria_{node}_{case_name}"] = df.apply(func, axis=1)

    df[f"h1_criteria_{case_name}"] = df[
        [f"h1_criteria_i_{case_name}", f"h1_criteria_j_{case_name}"]
    ].max(axis=1)
    return df


def check_multiple_load_case_combined_compression_and_flexure(
    df: DataFrame,
    case_names: list[str],
    beams_strengths: dict[str, dict[str, float]],
):
    for name in case_names:
        df = check_load_case_combined_compression_and_flexure(
            df=df, case_name=name, beams_strengths=beams_strengths
        )
    df[f"h1_criteria_max"] = df[
        [f"h1_criteria_{name}" for name in case_names]
    ].max(axis=1)
    df[f"h1_criteria_max_case"] = df[
        [f"h1_criteria_{name}" for name in case_names]
    ].idxmax(axis=1)
    return df


def check_multiple_load_case_combined_compression_and_flexure(
    df: DataFrame,
    case_names: list[str],
    beams_strengths: dict[str, dict[str, float]],
):
    for name in case_names:
        df = check_load_case_combined_compression_and_flexure(
            df=df, case_name=name, beams_strengths=beams_strengths
        )
    df[f"h1_criteria_max"] = df[
        [f"h1_criteria_{name}" for name in case_names]
    ].max(axis=1)
    df[f"h1_criteria_max_case"] = df[
        [f"h1_criteria_{name}" for name in case_names]
    ].idxmax(axis=1)
    return df