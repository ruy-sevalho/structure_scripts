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


# def set_size(df: pd.DataFrame):
#     return len(set(df["value"]))


# def check_dataframe(df: pd.DataFrame):
#     """Check if file with results from ansys is giving repeated values. Same node and element id appears multiple times
#     in txt exported results, with apparently the same value.
#     """
#     _, cols = df.shape
#     n = df["Node Number"].max()
#     cum_df = pd.DataFrame(columns=["node" "set size"])
#     for i in range(1, n + 1):
#         node_set = df.query(f"`Node Number` == {i}")
#         check_df = pd.DataFrame(
#             {"node": [i], "set size": [set_size(node_set)]}
#         )
#         cum_df = pd.concat((cum_df, check_df))
#     return cum_df


# def name_elements(df: pd.DataFrame, nodes_dict: dict[str, pd.DataFrame]):
#     for name, nodes in nodes_dict.items():
#         nodes = tuple(nodes["node"])
#         check_df = pd.DataFrame()
#         # check_df[ELEM] = df[ELEM]
#         check_df[NODE_I] = df[NODE_I].apply(lambda x: x in nodes)
#         check_df[NODE_J] = df[NODE_J].apply(lambda x: x in nodes)
#         check_df["both"] = check_df[NODE_I] & check_df[NODE_J]
#         idx = check_df.index[check_df["both"]]
#         df.loc[idx, BEAM] = name
#     return df


def _convert(x):
    return int(float(x))


def _append_load_case_name(names: list[str], case: str, start_from: int = 3):
    return names[:start_from] + [
        f"{name}_{case}" for name in names[start_from:]
    ]


# def _read_load_case_result(
#     file: Path, load_case: str, include_nodes: bool = False
# ):
#     names = _append_load_case_name(BEAM_RESULT_VALUES, case=load_case)
#     cols = list(names)
#     if not include_nodes:
#         cols.remove(NODE_I)
#         cols.remove(NODE_J)
#     with open(file, "r") as f:
#         results = pd.read_table(
#             f,
#             sep=",",
#             index_col=False,
#             names=names,
#             usecols=cols,
#             converters={
#                 ELEM: _convert,
#             },
#         ).set_index(ELEM)
#     return results


# def _read_beam_load_case_result__(
#     file: Path, load_case: str, include_nodes: bool = False
# ):
#     names = _append_load_case_name(BEAM_RESULT_VALUES, case=load_case)
#     cols = list(names)
#     if not include_nodes:
#         cols.remove(NODE_I)
#         cols.remove(NODE_J)
#     with open(file, "r") as f:
#         results = pd.read_table(
#             f,
#             sep=",",
#             index_col=False,
#             names=names,
#             usecols=cols,
#             converters={
#                 ELEM: _convert,
#             },
#         ).set_index(ELEM)
#     return results


# def _read_beams_results__(
#     case_path: Path,
#     case_name: str,
#     n_bodies: int,
#     prefix: str = "beams",
#     include_nodes: bool = False,
# ):
#     names = _append_load_case_name(BEAM_RESULT_VALUES, case=case_name)
#     cols = list(names)
#     sufix = ".txt"
#     if not include_nodes:
#         cols.remove(NODE_I)
#         cols.remove(NODE_J)
#     df = pd.DataFrame()
#     for i in range(n_bodies):
#         beam_name = f"{prefix}{str(i+1)}"
#         file = case_path / f"{beam_name}{sufix}"
#         with open(file, "r") as f:
#             results = pd.read_table(
#                 f,
#                 sep=",",
#                 index_col=False,
#                 names=names,
#                 usecols=cols,
#                 converters={
#                     ELEM: _convert,
#                 },
#             ).set_index(ELEM)
#             # old_idx = results.index.to_frame()
#             # old_idx.insert(0, beam_name, beam_name)
#             # results.index = pd.MultiIndex.from_frame(old_idx)
#             if include_nodes:
#                 results.insert(loc=0, column="beam", value=beam_name)
#             df = pd.concat((df, results))
#
#     return df


# def _read_results(load_cases_dict: dict[str, Path]):
#     df = pd.DataFrame()
#     for i, (key, value) in enumerate(load_cases_dict.items()):
#         i = not i
#         df = pd.concat(
#             (
#                 df,
#                 _read_load_case_result(
#                     file=value, load_case=key, include_nodes=i
#                 ),
#             ),
#             axis=1,
#         )
#     return df


# def _read_beam_results(load_cases_dict: dict[str, Path]):
#     return
#
#
# def _read_beam_truss(load_cases_dict: dict[str, Path]):
#     return
#
#
# def read_node(file: Path) -> pd.DataFrame:
#     with open(file, "r") as f:
#         nodes = pd.read_table(f, sep=",", index_col=False, names=["node"])
#     return nodes
#
#
# def read_nodes(nodes: dict[str, Path]) -> dict[str, pd.DataFrame]:
#     return {key: read_node(value) for key, value in nodes.items()}
#
#
# def generate_path_dict(
#     folder: Path, n: int, prefix: str = "beams", suffix: str = ".txt"
# ):
#     return {
#         f"{prefix}{i}": folder / Path(f"{prefix}{i}{suffix}")
#         for i in range(1, n + 1)
#     }


# def _generate_load_cases_paths(
#     directories: list[Path], load_cases: Collection[str]
# ):
#     suffix = ".txt"
#     return {
#         load_case: directory / Path(f"{load_case}{suffix}")
#         for load_case, directory in zip(load_cases, directories)
#     }


# def _generate_load_cases_paths__(
#     directories: list[Path],
#     load_cases: Collection[str],
#     n_bodies: int,
#     body_prefix: str,
# ):
#     suffix = ".txt"
#     return {
#         load_case: directory / Path(f"{suffix}")
#         for load_case, directory in zip(load_cases, directories)
#     }


# def get_and_process_results(
#     n_named_selection: int,
#     load_cases: dict[str:Path],
#     nodes_path: Path,
#     prefix: str = "beams",
# ):
#     load_cases_paths = _generate_load_cases_paths(
#         directories=load_cases.values(), load_cases=load_cases.keys()
#     )
#     nodes_path_dict = generate_path_dict(
#         nodes_path, n=n_named_selection, prefix=prefix
#     )
#     nodes = read_nodes(nodes_path_dict)
#     df = _read_results(load_cases_paths)
#     return name_elements(df, nodes)


# def get_and_process_results__(
#     load_cases: dict[str:Path],
#     n_beams: int = 0,
#     n_truss: int = 0,
#     beam_prefix: str = "beams",
#     truss_prefix: str = "beams",
# ):
#     df = pd.DataFrame()
#     for i, (name, path) in enumerate(load_cases.items()):
#         results = _read_beams_results__(
#             case_path=path,
#             case_name=name,
#             n_bodies=n_beams,
#             prefix=beam_prefix,
#             include_nodes=not i,
#         )
#         df = pd.concat((df, results), axis=1)
#     return df


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
