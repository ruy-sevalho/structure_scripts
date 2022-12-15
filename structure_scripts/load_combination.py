from typing import Collection

from pandas import DataFrame, concat

from structure_scripts.ansys import BEAM_RESULTS


def add_load_case(
    df: DataFrame, load_case: Collection[tuple[str, float]], name: str
):
    for result in BEAM_RESULTS:
        exp = " + ".join([f"{result}_{case} * {factor}" for case, factor in load_case])
        df[f"{result}_{name}"] = df.eval(exp)
    return df


def add_load_cases(
        df: DataFrame, load_cases: Collection[tuple[str, Collection[tuple[str, float]]]]
):
    for load_case in load_cases:
        df = concat((df, add_load_case(df, load_case=load_case[1], name=load_case[0])))
    return df
