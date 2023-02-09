from pathlib import Path

from quantities import Quantity, m

from structure_scripts.aisc.aisc_database import AISC_Sections
from structure_scripts.aisc.angle import AngleAISC36010
from structure_scripts.aisc.channel import ChannelAISC36010
from structure_scripts.aisc.criteria import DesignStrength
from structure_scripts.aisc.i_section import DoublySymmetricIAISC36010
from structure_scripts.aisc.sections import (
    ConstructionType,
    axial_flexural_critical_load,
    AxialFlexuralCombination,
)
from structure_scripts.process_external_files.ansys import (
    get_and_process_results_per_beam_selection,
)
from structure_scripts.process_external_files.load_combination import (
    add_load_cases,
    check_multiple_load_case_combined_compression_and_flexure,
)
from structure_scripts.materials import steel250MPa


PREFIX = "beams"


w = DoublySymmetricIAISC36010(
    material=steel250MPa,
    section=AISC_Sections["W6X15"],
    construction=ConstructionType.ROLLED,
)
big_channel = ChannelAISC36010(
    material=steel250MPa,
    section=AISC_Sections["C6X8.2"],
    construction=ConstructionType.ROLLED,
)
small_channel = ChannelAISC36010(
    material=steel250MPa,
    section=AISC_Sections["C4X4.5"],
    construction=ConstructionType.ROLLED,
)

distance_between_columns_x = (2 * 1.4 + 0.675 + 1.205) * m
long_unbraced_length = distance_between_columns_x / 7
width = 1.4 * m

beams1 = axial_flexural_critical_load(
    profile=w,
    length_major_axis=2.1 * m,
    length_minor_axis=2.1 * m,
    length_torsion=2.1 * m,
    k_factor_major_axis=2.1,
    k_factor_minor_axis=2.1,
    k_factor_torsion=2.1,
    moment_unit="N*mm",
)
beams2 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=long_unbraced_length,
    length_torsion=distance_between_columns_x,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
    moment_unit="N*mm",
)

beams3 = axial_flexural_critical_load(
    profile=small_channel,
    length_major_axis=width,
    length_minor_axis=width,
    length_torsion=width,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
    moment_unit="N*mm",
)

beams4 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=Quantity(430, "mm"),
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
    moment_unit="N*mm",
)

beams5 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=Quantity(200, "mm"),
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
    moment_unit="N*mm",
)

beams = [beams1, beams2, beams3, beams4, beams5]


beams1data = AxialFlexuralCombination(
    profile=w,
    length_major_axis=2.1 * m,
    length_minor_axis=2.1 * m,
    length_torsion=2.1 * m,
    k_factor_major_axis=2.1,
    k_factor_minor_axis=2.1,
    k_factor_torsion=2.1,
)
beams2data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=long_unbraced_length,
    length_torsion=long_unbraced_length,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams3data = AxialFlexuralCombination(
    profile=small_channel,
    length_major_axis=width,
    length_minor_axis=width,
    length_torsion=width,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams4data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=Quantity(430, "mm"),
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams5data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=Quantity(200, "mm"),
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams_data = [
    beams1data,
    beams2data,
    beams3data,
]

critical_strengths: dict[str, DesignStrength] = {
    f"{PREFIX}{i+1}": beam.result for i, beam in enumerate(beams_data)
}

small_angle = AngleAISC36010(
    section=AISC_Sections["L2X2X1/8"],
    construction=ConstructionType.ROLLED,
    material=steel250MPa,
)

large_angle = AngleAISC36010(
    section=AISC_Sections["L2-1/2X2-1/2X3/16"],
    construction=ConstructionType.ROLLED,
    material=steel250MPa,
)

angles_ds = (
    ("big diagonal", large_angle.compression(2.520 * m)),
    ("Common diagonal", small_angle.compression(length_major_axis=1.5514 * m)),
    (
        "Common half diagonal",
        small_angle.compression(length_major_axis=1.5514 / 2 * m),
    ),
    (
        "Smaller half diagonal",
        small_angle.compression(length_major_axis=0.732 * m),
    ),
)

for name, ds in angles_ds:
    print(f"{name} strength = {ds.design_strength_asd.rescale('N')}")

#
# index_tuples = [
#     (f"{PREFIX}{i+1}", result)
#     for i, _ in enumerate(beams_data)
#     for result in (FX, MY, MZ)
# ]
# str_values = [
#     beam[result] for i, beam in enumerate(beams) for result in (FX, MY, MZ)
# ]
# data = [[value] for value in str_values]
# index = pd.MultiIndex.from_tuples(index_tuples, names=["beam", "str"])
# dct = {key: [value] for key, value in zip(index_tuples, str_values)}
# strs = pd.DataFrame(data=[str_values], columns=index)

critical_loads = {f"{PREFIX}{i+1}": beam for i, beam in enumerate(beams)}


# directories = [
#     Path(
#         r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2022 save me_files\dp0\SYS\MECH"
#     ),
#     Path(
#         r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2022 save me_files\dp0\SYS-1\MECH"
#     ),
#     Path(
#         r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2022 save me_files\dp0\SYS-3\MECH"
#     ),
# ]

base_path = Path(r"C:\Users\U3ZO\Documents\PROJE\new_files\user_files")
base_load_cases = {
    "vert": base_path / "acc_vert",
    "trans": base_path / "acc_long",
    "long": base_path / "acc_vert",
    "wind_x": base_path / "wind_x",
    "wind_y": base_path / "wind_y",
    "wind_neg_x": base_path / "-wind_x",
    "wind_neg_y": base_path / "-wind_y",
}

df = get_and_process_results_per_beam_selection(
    load_cases=base_load_cases, n_beams=4
)


comb_load_cases = [
    (
        "1",
        (("vert", 1.28000), ("trans", 0.31), ("long", 0.15), ("wind_x", 1.0)),
    ),
    (
        "2",
        (
            ("vert", 1.28000),
            ("trans", 0.31),
            ("long", -0.15),
            ("wind_neg_x", 1.0),
        ),
    ),
    (
        "3",
        (("vert", 1.28000), ("trans", -0.31), ("long", 0.15), ("wind_x", 1.0)),
    ),
    (
        "4",
        (
            ("vert", 1.28000),
            ("trans", -0.31),
            ("long", -0.15),
            ("wind_neg_x", 1.0),
        ),
    ),
    (
        "5",
        (("vert", 1.28000), ("trans", 0.31), ("long", 0.15), ("wind_y", 1.0)),
    ),
    (
        "6",
        (
            ("vert", 1.28000),
            ("trans", -0.31),
            ("long", 0.15),
            ("wind_neg_y", 1.0),
        ),
    ),
    (
        "7",
        (("vert", 1.28000), ("trans", 0.31), ("long", -0.15), ("wind_y", 1.0)),
    ),
    (
        "8",
        (
            ("vert", 1.28000),
            ("trans", -0.31),
            ("long", -0.15),
            ("wind_neg_y", 1.0),
        ),
    ),
]
df = add_load_cases(df=df, load_cases=comb_load_cases)
df = check_multiple_load_case_combined_compression_and_flexure(
    df, list(str(i) for i in range(1, 9)), critical_loads
).sort_values("h1_criteria_max", ascending=False)
trans = df[df["beam"] == "beams3"]
cols = df[df["beam"] == "beams1"]
long = df[df["beam"] == "beams2"]
h1_case_criteria = [f"h1_criteria_{str(i)}" for i in range(1, 9)]
max_criteria = df[
    ["beam", *h1_case_criteria, "h1_criteria_max", "h1_criteria_max_case"]
]
max_criteria["h1_criteria_max_case"] = df["h1_criteria_max_case"].apply(
    lambda x: x[12:]
)
h1_result_path = Path(
    r"C:\Users\U3ZO\Documents\PROJE\new_files\user_files\\h1.csv"
)
max_criteria.to_csv(h1_result_path, index_label="Element")
