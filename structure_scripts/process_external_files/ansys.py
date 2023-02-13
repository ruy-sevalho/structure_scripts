from dataclasses import dataclass
from typing import Collection, Literal

import pandas as pd

from pathlib import Path


BEAM = "beam"
NODE = "node"
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
T = "t"

ANSYS_ELEM_ID = "Element Number"
ANSYS_NODE_ID = "Node Number"
ANSYS_AXIAL_FORCE = "Directional Axial Force (N)"
ANSYS_SHEAR_FORCE = "Directional Shear Force (N)"
ANSYS_TORSION_MOMENT = "Total Torsional Moment (Nmm)"
ANSYS_MY = "Directional Bending Moment (Nmm)"
ANSYS_MZ = "Directional Bending Moment (Nmm)"

BEAM_RESULT = (FX, MY, SY, MZ, SZ, T)
BEAM_RESULTS = (FXI, FXJ, MYI, MYJ, MZI, MZJ)

BEAM_RESULT_DICT = {
    FX: ANSYS_AXIAL_FORCE,
    MY: ANSYS_MY,
    MZ: ANSYS_MZ,
    SY: ANSYS_SHEAR_FORCE,
    SZ: ANSYS_SHEAR_FORCE,
    T: ANSYS_TORSION_MOMENT,
}

# Order must match order of the table exported by ansys
BEAM_RESULT_VALUES = [ELEM, NODE_I, NODE_J, FXI, FXJ, MYI, MYJ, MZI, MZJ]


def _convert(x):
    return int(float(x))


def _read_beam_result_two_nodes_per_element(
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


def _read_named_selection_beams_results(
    case_path: Path,
    case_name: str,
    named_selections: Collection[str],
    include_nodes: bool = False,
    results: Collection[str] = (FX, MY, MZ),
):
    df = pd.DataFrame()
    for named_selection in named_selections:
        beam_name = named_selection
        base_file_path = case_path / f"{named_selection}"
        df_per_beam = _read_beam_results(
            base_file_path=base_file_path,
            beam_name=beam_name,
            case_name=case_name,
            include_nodes=include_nodes,
            results=results,
        )
        df = pd.concat((df, df_per_beam))
    return df


def _read_beam_node_result(
    file: Path,
    case_name: str,
    result_type: Literal[FX, MY, SY, MZ, SZ, T],
    include_nodes: bool = False,
):
    df = pd.read_table(
        file,
        delimiter="\t",
        encoding="UTF-8",
        encoding_errors="ignore",
    )
    df.set_index(
        keys=[ANSYS_NODE_ID, ANSYS_ELEM_ID],
        inplace=True,
        drop=not include_nodes,
    )
    df.index.set_names(names=[NODE, ELEM], inplace=True)
    df.rename(
        columns={BEAM_RESULT_DICT[result_type]: f"{result_type}_{case_name}"},
        inplace=True,
    )
    return df


def _read_beam_node_results(
    base_file_path: Path,
    case_name: str,
    results: Collection[str] = BEAM_RESULT,
    include_nodes: bool = False,
):
    df = pd.DataFrame()
    for i, result in enumerate(results):
        n_df = _read_beam_node_result(
            file=base_file_path / f"{result}.txt",
            case_name=case_name,
            result_type=result,
            include_nodes=include_nodes and not i,
        )
        df = pd.concat((df, n_df), axis=1)
    return df


def _read_beam_results(
    base_file_path: Path,
    beam_name: str,
    case_name: str,
    include_nodes: bool,
    results: Collection[str],
):
    suffix = ".txt"
    df = pd.DataFrame()
    for j, r_type in enumerate(results):
        file = base_file_path / f"{r_type}{suffix}"
        include = include_nodes and not j
        r_df = _read_beam_result_two_nodes_per_element(
            file=file,
            result_type=r_type,
            case_name=case_name,
            include_nodes=include,
        )
        if include:
            r_df.insert(loc=0, column="beam", value=beam_name)
        df = pd.concat((df, r_df), axis=1)
    return df


def read_and_process_results_per_beam_selection(results_folder: Path):
    """Reads results per beam named selection in a structured directory.
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
    combination_folders = _get_folders(results_folder)
    named_selections = [
        f.name for f in _get_folders(results_folder / combination_folders[0])
    ]
    df = pd.DataFrame()
    for i, combination in enumerate(combination_folders):
        r_df = _read_named_selection_beams_results(
            case_path=results_folder / combination,
            case_name=combination.name,
            include_nodes=not i,
            named_selections=named_selections,
        )
        df = pd.concat((df, r_df), axis=1)
    return df


def _get_folders(folder) -> list[Path]:
    return [f for f in folder.iterdir() if f.is_dir()]


def read_all_beam_results(results_folder: Path):
    """Reads results of all beams.
    In the parent directory there should be a folder per load case.
    In each load case folder there should a txt file per result:\n
    fx.txt, my.txt, mz.txt, sy.txt, sz.txt, t.txt.\n
    fx - axial force\n
    my - bending moment y-axis\n
    mz - bending moment z-axis\n
    sy - shear force y-axis\n
    sz - shear force z-axis\n
    t - torsion moment\n
    """
    combination_folders = [f for f in results_folder.iterdir() if f.is_dir()]
    df = pd.DataFrame()
    for i, combination in enumerate(combination_folders):
        r_df = _read_beam_node_results(
            base_file_path=results_folder / combination,
            case_name=combination.name,
            include_nodes=not i,
        )
        df = pd.concat((df, r_df), axis=1)
    df.rename(columns={ANSYS_NODE_ID: NODE, ANSYS_ELEM_ID: ELEM}, inplace=True)
    return df


def read_load_combination(file: Path) -> pd.DataFrame:
    """Read an Ansys solution combination exported csv file and returns a Dataframe of the combination"""
    df = pd.read_csv(file)
    df.drop(labels=range(4), inplace=True)
    df.drop(columns="Environment", inplace=True)
    df.rename(columns={"Unnamed: 0": "Comb"}, inplace=True)
    return df


@dataclass(frozen=True, slots=True)
class ConnectionDef:
    nodes: Collection[int]
    elem: Collection[int]


def read_connections(directory: Path):
    connections = _get_folders(directory)
    connections_dict = dict()
    for connection in connections:
        connections_dict[connection.name] = ConnectionDef(
            nodes=pd.read_table(
                directory / connection / "nodes.txt", usecols=[ANSYS_NODE_ID]
            )[ANSYS_NODE_ID].values,
            elem=pd.read_table(
                directory / connection / "elements.txt",
                sep="\t",
                skiprows=1,
                header=None
            )[0].values
        )
    return connections_dict


def _filter_results_for_connection(
    results: pd.DataFrame, nodes: Collection[int], elem: Collection[int]
):
    return pd.DataFrame(
        results[results.apply(lambda row: row[NODE] in nodes and row[ELEM] in elem, axis=1)]
    )


def filter_results_for_connections(
    results: pd.DataFrame, collections: dict[str, ConnectionDef]
):
    return {
        key: _filter_results_for_connection(results, value.nodes, value.elem)
        for key, value in collections.items()
    }
