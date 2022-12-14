from pathlib import Path

from structure_scripts.ansys import (
    get_and_process_results,
)

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
load_cases = ["vert", "trans", "long"]
df = get_and_process_results(
    directories=directories, n_named_selection=11, load_cases=load_cases
)
