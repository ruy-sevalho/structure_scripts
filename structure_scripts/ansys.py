import pathlib

import pandas as pd
from os import listdir
from pathlib import Path


def rename_col(df: pd.DataFrame):
    _, cols = df.shape
    return df.rename(columns={df.columns[-1]: "value"})


def set_size(df: pd.DataFrame):
    return len(set(df["value"]))


def check_dataframe(df: pd.DataFrame):
    """Check if file with results from ansys is giving repeated values (same node and element id appears multiple times
    in results).
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


def read_results(file: pathlib.Path):
    with open(file, "r") as f:
        results = pd.read_table(
            f,
            sep=",",
            index_col=False,
            names=[
                ELEM,
                "node_i",
                "node_j",
                "fxi",
                "fxj",
                "myi",
                "myj",
                "mzi",
                "mzj",
            ],
            converters={ELEM: _convert},
        ).set_index(ELEM)
    return results


def read_node(file: pathlib.Path) -> pd.DataFrame:
    with open(file, "r") as f:
        nodes = pd.read_table(f, sep=",", index_col=False, names=["node"])
    return nodes


def read_nodes(nodes: dict[str, pathlib.Path]) -> dict[str, pd.DataFrame]:
    return {key: read_node(value) for key, value in nodes.items()}


def generate_path_dict(
    folder: pathlib.Path, n: int, prefix: str = "beams", suffix: str = ".txt"
):
    return {
        f"{prefix}{i}": folder / Path(f"{prefix}{i}{suffix}")
        for i in range(1, n + 1)
    }


if __name__ == "__main__":
    results_fp = Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH\vert.txt"
    )
    nodes_directory = Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH"
    )
    nodes_path_dict = generate_path_dict(nodes_directory, 11)
    nodes = read_nodes(nodes_path_dict)
    df = read_results(results_fp)
    df = name_elements(df, nodes)

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
