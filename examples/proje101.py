from pathlib import Path

from quantities import Quantity

from structure_scripts.ansys import (
    get_and_process_results,
)
from structure_scripts.load_combination import add_load_case, add_load_cases

directories = [
    Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH"
    ),
    Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS-1\MECH"
    ),
    Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS-3\MECH"
    ),
]

ACC_VERT = "acc_vert"


base_load_cases = {
    "vert": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH"
    ),
    "trans": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS-1\MECH"
    ),
    "long": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS-3\MECH"
    ),
}


df = get_and_process_results(
     n_named_selection=11, load_cases=base_load_cases, nodes_path=base_load_cases["vert"]
)
comb_load_cases = [
    ("1", (("vert", 1.28000), ("trans", 0.31), ("long", 0.15))),
    ("2", (("vert", 1.28000), ("trans", -0.31), ("long", 0.15))),
]
exp = " + ".join([f"test_{case} * {factor}" for case, factor in comb_load_cases])

df = add_load_cases(df=df, load_cases=comb_load_cases)

PREFIX = "beams"

critical_loads = {
    f"{PREFIX}{1}": {"fx": Quantity()}
}