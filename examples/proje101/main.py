from pathlib import Path

from read_results import user_directory, df_per_beam, df_all, connections_results


# post-processing results
trans = df_per_beam[df_per_beam["beam"] == "beams3"]
cols = df_per_beam[df_per_beam["beam"] == "beams1"]
long = df_per_beam[df_per_beam["beam"] == "beams2"]
h1_case_criteria = [f"h1_criteria_Combination {str(i)}" for i in range(1, 9)]
max_criteria = df_per_beam[
    ["beam", *h1_case_criteria, "h1_criteria_max", "h1_criteria_max_case"]
]
max_criteria["h1_criteria_max_case"] = df_per_beam[
    "h1_criteria_max_case"
].apply(lambda x: x[12:])
h1_result_path = user_directory / Path(r"h1.csv")
max_criteria.to_csv(h1_result_path, index_label="Element")
