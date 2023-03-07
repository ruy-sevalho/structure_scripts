from pathlib import Path

from examples.proje101.connections import (
    connections_criteria,
)
from structure_scripts.process_external_files.ansys import (
    read_and_process_results_per_beam_selection,
    read_all_beam_results,
    read_load_combination,
    BEAM_RESULT,
    read_connections,
    filter_results_for_connections,
)
from structure_scripts.process_external_files.connections import (
    _check_connection,
    check_connections,
)
from structure_scripts.process_external_files.load_combination import (
    add_load_cases,
    check_multiple_load_case_combined_compression_and_flexure,
)

from critical_loads import critical_loads

user_directory = Path(
    r"C:\Users\U3ZO\proje\proje 101 plataforma hood compressores\ansys\new_files\user_files"
)
base_path = user_directory / Path(r"load_combinations")

df_per_beam, combinations = read_and_process_results_per_beam_selection(
    results_folder=base_path
)
df_all = read_all_beam_results(results_folder=base_path)
comb_load_cases_ = read_load_combination(
    user_directory / Path(r"loading2.csv")
)
df_per_beam = add_load_cases(
    base_results=df_per_beam, load_cases=comb_load_cases_
)
df_per_beam = check_multiple_load_case_combined_compression_and_flexure(
    df_per_beam,
    list(f"Combination {str(i)}" for i in range(1, 9)),
    critical_loads,
).sort_values("h1_criteria_max", ascending=False)
df_all = add_load_cases(
    df_all, load_cases=comb_load_cases_, results=BEAM_RESULT
)

# read-connections
connections = read_connections(user_directory / r"connections")
connections_results = filter_results_for_connections(df_all, connections)
case_names = comb_load_cases_["Comb"]

# evaluate connections
list_of_connections = ["long", "trans", "platform_diag", "column_base"]
connections_checks = check_connections(
    results={key: connections_results[key] for key in list_of_connections},
    connections=connections_criteria,
    case_names=case_names,
)
