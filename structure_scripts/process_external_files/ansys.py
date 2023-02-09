from typing import Collection, Literal

import pandas as pd
from os import listdir
from pathlib import Path

from quantities import Quantity

BEAM = "beam"
NODE_I = "node_i"
NODE_J = "node_j"
ELEM = "elem"
FX = "fx"
MY = "my"
MZ = "mz"
SY = "sy"
SZ = "sz"
FXI = "fxi"
FXJ = "fxj"
MYI = "myi"
MYJ = "myj"
MZI = "mzi"
MZJ = "mzj"
T = "torsion"

ANSYS_ELEM_ID = "Element Number"
ANSYS_NODE_ID = "Node Number"
ANSYS_FORCE = "Directional Axial Force (N)"
ANSYS_MY = "Directional Bending Moment (Nmm)"
ANSYS_MZ = "Directional Bending Moment (Nmm)"

BEAM_RESULT = [FX, MY, SY, MZ, SZ, T]
BEAM_RESULTS = [FXI, FXJ, MYI, MYJ, MZI, MZJ]

BEAM_RESULT_DICT = {FX: ANSYS_FORCE, MY: ANSYS_MY, MZ: ANSYS_MZ}

# Order must match order of the table exported by ansys
BEAM_RESULT_VALUES = [ELEM, NODE_I, NODE_J, FXI, FXJ, MYI, MYJ, MZI, MZJ]

DF_COLS = [ELEM, NODE_I, NODE_J]


def rename_col(df: pd.DataFrame):
    _, cols = df.shape
    return df.rename(columns={df.columns[-1]: "value"})


def _convert(x):
    return int(float(x))


def _append_load_case_name(names: list[str], case: str, start_from: int = 3):
    return names[:start_from] + [
        f"{name}_{case}" for name in names[start_from:]
    ]


def _read_beam_result(
    file: Path,
    result_type: Literal[FX, MY, SY, MZ, SZ, T],
    case_name: str,
    include_nodes: bool = False,
):
    df = pd.read_table(
        file,
        converters={
            ELEM: _convert,
        },
        delimiter="\t",
        encoding="UTF-8",
        encoding_errors="ignore",
    )
    n_df = pd.DataFrame()
    n_df[ELEM] = df[ANSYS_ELEM_ID].drop_duplicates()
    n_df.set_index(ELEM, inplace=True, drop=True)
    value_name = BEAM_RESULT_DICT[result_type]
    for elem in n_df.index:
        i, j = df[df[ANSYS_ELEM_ID] == elem][ANSYS_NODE_ID].values
        if include_nodes:
            n_df.at[elem, NODE_I] = i
            n_df.at[elem, NODE_J] = j
        elem_df = df.loc[df[ANSYS_ELEM_ID] == elem]
        n_df.at[elem, f"{result_type}i_{case_name}"] = elem_df[
            elem_df[ANSYS_NODE_ID] == i
        ][value_name].iloc[0]
        n_df.at[elem, f"{result_type}j_{case_name}"] = elem_df[
            elem_df[ANSYS_NODE_ID] == j
        ][value_name].iloc[0]
    return n_df


def _read_beams_results____(
    case_path: Path,
    case_name: str,
    n_bodies: int,
    prefix: str = "beams",
    include_nodes: bool = False,
    results: Collection[str] = (FX, MY, MZ),
):
    suffix = ".txt"
    df = pd.DataFrame()
    for i in range(n_bodies):
        beam_name = f"{prefix}{str(i+1)}"
        base_file_path = case_path / f"{beam_name}"
        df_per_beam = pd.DataFrame()
        for i, r_type in enumerate(results):
            file = base_file_path / f"{r_type}.txt"
            include = include_nodes and not i
            r_df = _read_beam_result(
                file=file,
                result_type=r_type,
                case_name=case_name,
                include_nodes=include,
            )
            if include:
                r_df.insert(loc=0, column="beam", value=beam_name)
            df_per_beam = pd.concat((df_per_beam, r_df), axis=1)
        df = pd.concat((df, df_per_beam))
    return df


def get_and_process_results_per_beam_selection(
    load_cases: dict[str:Path],
    n_beams: int = 0,
    results: Collection[str] = (FX, MY, MZ),
    beam_prefix: str = "beams",
):
    df = pd.DataFrame()
    for i, (name, path) in enumerate(load_cases.items()):
        r_df = _read_beams_results____(
            case_path=path,
            case_name=name,
            n_bodies=n_beams,
            prefix=beam_prefix,
            include_nodes=not i,
            results=results,
        )
        df = pd.concat((df, r_df), axis=1)
    return df


if __name__ == "__main__":
    pass
