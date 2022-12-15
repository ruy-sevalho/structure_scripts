from typing import Collection

import pandas as pd
from os import listdir
from pathlib import Path

from quantities import Quantity


def rename_col(df: pd.DataFrame):
    _, cols = df.shape
    return df.rename(columns={df.columns[-1]: "value"})


def set_size(df: pd.DataFrame):
    return len(set(df["value"]))


def check_dataframe(df: pd.DataFrame):
    """Check if file with results from ansys is giving repeated values. Same node and element id appears multiple times
    in txt exported results, with apparently the same value.
    """
    _, cols = df.shape
    n = df["Node Number"].max()
    cum_df = pd.DataFrame(columns=["node" "set size"])
    for i in range(1, n + 1):
        node_set = df.query(f"`Node Number` == {i}")
        check_df = pd.DataFrame(
            {"node": [i], "set size": [set_size(node_set)]}
        )
        cum_df = pd.concat((cum_df, check_df))
    return cum_df


BEAM = "beam"
NODE_I = "node_i"
NODE_J = "node_j"
ELEM = "elem"
FX = "fx"
MY = "my"
MZ = "mz"
FXI = "fxi"
FXJ = "fxj"
MYI = "myi"
MYJ = "myj"
MZI = "mzi"
MZJ = "mzj"


def name_elements(df: pd.DataFrame, nodes_dict: dict[str, pd.DataFrame]):
    for name, nodes in nodes_dict.items():
        nodes = tuple(nodes["node"])
        check_df = pd.DataFrame()
        # check_df[ELEM] = df[ELEM]
        check_df[NODE_I] = df[NODE_I].apply(lambda x: x in nodes)
        check_df[NODE_J] = df[NODE_J].apply(lambda x: x in nodes)
        check_df["both"] = check_df[NODE_I] & check_df[NODE_J]
        idx = check_df.index[check_df["both"]]
        df.loc[idx, BEAM] = name
    return df


def _convert(x):
    return int(float(x))


BEAM_RESULTS = [FXI, FXJ, MYI, MYJ, MZI, MZJ]

# Order must match order of the table exported by ansys
RESULT_VALUES = [ELEM, NODE_I, NODE_J, FXI, FXJ, MYI, MYJ, MZI, MZJ]


def _append_load_case_name(names: list[str], case: str, start_from: int = 3):
    return names[:start_from] + [
        f"{name}_{case}" for name in names[start_from:]
    ]


def _read_load_case_result(
    file: Path, load_case: str, include_nodes: bool = False
):
    names = _append_load_case_name(RESULT_VALUES, case=load_case)
    cols = list(names)
    if not include_nodes:
        cols.remove(NODE_I)
        cols.remove(NODE_J)
    with open(file, "r") as f:
        results = pd.read_table(
            f,
            sep=",",
            index_col=False,
            names=names,
            usecols=cols,
            converters={
                ELEM: _convert,
            },
        ).set_index(ELEM)
    return results


def _read_results(load_cases_dict: dict[str, Path]):
    df = pd.DataFrame()
    for i, (key, value) in enumerate(load_cases_dict.items()):
        i = not i
        df = pd.concat(
            (
                df,
                _read_load_case_result(
                    file=value, load_case=key, include_nodes=i
                ),
            ),
            axis=1,
        )
    return df


def read_node(file: Path) -> pd.DataFrame:
    with open(file, "r") as f:
        nodes = pd.read_table(f, sep=",", index_col=False, names=["node"])
    return nodes


def read_nodes(nodes: dict[str, Path]) -> dict[str, pd.DataFrame]:
    return {key: read_node(value) for key, value in nodes.items()}


def generate_path_dict(
    folder: Path, n: int, prefix: str = "beams", suffix: str = ".txt"
):
    return {
        f"{prefix}{i}": folder / Path(f"{prefix}{i}{suffix}")
        for i in range(1, n + 1)
    }


def _generate_load_cases_paths(
    directories: list[Path], load_cases: Collection[str]
):
    suffix = ".txt"
    return {
        load_case: directory / Path(f"{load_case}{suffix}")
        for load_case, directory in zip(load_cases, directories)
    }


def get_and_process_results(
    n_named_selection: int,
    load_cases: dict[str: Path],
    nodes_path: Path,
    prefix: str = "beams",
):
    load_cases_paths = _generate_load_cases_paths(
        directories=load_cases.values(), load_cases=load_cases.keys()
    )
    nodes_path_dict = generate_path_dict(
        nodes_path, n=n_named_selection, prefix=prefix
    )
    nodes = read_nodes(nodes_path_dict)
    df = _read_results(load_cases_paths)
    return name_elements(df, nodes)


if __name__ == "__main__":
    d = {i: str(i + 1) for i in range(5)}
    print(list(enumerate(d.items())))
    pass
    # results_fp = Path(
    #     r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH\vert.txt"
    # )
    # nodes_directory = Path(
    #     r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH"
    # )
    # nodes_path_dict = generate_path_dict(nodes_directory, 11)
    # nodes = read_nodes(nodes_path_dict)
    # df = read_results(results_fp)
    # df = name_elements(df, nodes)

    # directory = Path("crazy/")
    # files = listdir(directory)
    #
    # axial_results = dict()

    #
    # with open(directory/"vert.txt" "r") as f:
    #     results = pd.read_table(f sep="" index_col=False header=None names=["elem" "node_i" "node_j" "fxi" "fxj" "myi" "myj" "mzi" "mzj"])
    #
    # nodes_series = nodes["node"]
    # check = check_elem_in(results nodes)
    # check = check[(check.both)]

    # results["sel"] = results.apply()

    # for file in files:
    #     with open(directory / file "r") as f:
    #         df = pd.concat((df pd.read_table(f)) axis=1)
    #
    # df = df.sort_values("Element Number")
    # df2 = df.drop_duplicates()
    # df3 = df.drop_duplicates().sort_values("Directional Axial Force (N)")
