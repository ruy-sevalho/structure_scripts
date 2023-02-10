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


def _convert(x):
    return int(float(x))


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


def _read_beams_results(
    case_path: Path,
    case_name: str,
    named_selections: Collection[str],
    include_nodes: bool = False,
    results: Collection[str] = (FX, MY, MZ),
):
    suffix = ".txt"
    df = pd.DataFrame()
    for named_selection in named_selections:
        beam_name = named_selection
        base_file_path = case_path / f"{named_selection}"
        df_per_beam = pd.DataFrame()
        for j, r_type in enumerate(results):
            file = base_file_path / f"{r_type}{suffix}"
            include = include_nodes and not j
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


def read_and_process_results_per_beam_selection(results_folder: Path):
    """Read a results per beam named selection in a structured directory.
    In the parent directory there should be a folder per load case.
    In each load case folder there should a folder per beam named selection.
    In each beam result folder there should a txt file per result:\n
    fx.txt, my.txt, mz.txt, sy.txt, sz.txt, t.txt.\n
    fx - axial force\n
    my - bending moment y-axis\n
    mz - bending moment z-axis\n
    sy - shear force y-axis\n
    sz - shear force z-axis\n
    t - torsion moment\n
    """
    combination_folders = [f for f in results_folder.iterdir() if f.is_dir()]
    named_selections = [
        f.name
        for f in (results_folder / combination_folders[0]).iterdir()
        if f.is_dir()
    ]
    df = pd.DataFrame()
    for i, combination in enumerate(combination_folders):

        r_df = _read_beams_results(
            case_path=results_folder / combination,
            case_name=combination.name,
            include_nodes=not i,
            named_selections=named_selections,
        )
        df = pd.concat((df, r_df), axis=1)
    return df


def read_load_combination(file: Path) -> pd.DataFrame:
    """Read an Ansys solution combination exported csv file and returns a Dataframe of the combination"""
    df = pd.read_csv(file)
    df.drop(labels=range(4), inplace=True)
    df.drop(columns="Environment", inplace=True)
    df.rename(columns={"Unnamed: 0": "Comb"}, inplace=True)
    return df


if __name__ == "__main__":
    file = Path(r"C:\Users\U3ZO\Documents\PROJE\new_files\user_files")
    ns = [f"beams{i}" for i in range(1, 5)]
    l = read_and_process_results_per_beam_selection(file, ns)
    with open(file, "w") as f:
        f.writelines()
