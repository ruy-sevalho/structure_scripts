from pathlib import Path

import pandas as pd
from quantities import m

from structure_scripts.aisc.aisc_database import AISC_Sections
from structure_scripts.aisc.channel import ChannelAISC36010
from structure_scripts.aisc.criteria import DesignStrength
from structure_scripts.aisc.i_section import DoublySymmetricIAISC36010
from structure_scripts.aisc.sections import (
    ConstructionType,
    axial_flexural_critical_load,
    AxialFlexuralCombination,
)
from structure_scripts.process_external_files.ansys import (
    get_and_process_results,
    MZ,
    MY,
    FX,
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
    section=AISC_Sections["C4X5.4"],
    construction=ConstructionType.ROLLED,
)

distance_between_columns_x = (2 * 1.4 + 0.675 + 1.205) * m

beams1 = axial_flexural_critical_load(
    profile=w,
    length_major_axis=2.1 * m,
    length_minor_axis=2.1 * m,
    length_torsion=2.1 * m,
    k_factor_major_axis=2.1,
    k_factor_minor_axis=2.1,
    k_factor_torsion=2.1,
)
beams2 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=1.4 * m,
    length_torsion=1.4 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams3 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=1.205 * m,
    length_torsion=1.205 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams4 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=0.675 * m,
    length_torsion=0.675 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams5 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=0.428 * m,
    length_minor_axis=0.428 * m,
    length_torsion=0.428 * m,
    k_factor_major_axis=2,
    k_factor_minor_axis=2,
    k_factor_torsion=2,
)

beams6 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=0.152 * m,
    length_minor_axis=0.152 * m,
    length_torsion=0.152 * m,
    k_factor_major_axis=2,
    k_factor_minor_axis=2,
    k_factor_torsion=2,
)
beams7 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=1.4 * m,
    length_minor_axis=0.7 * m,
    length_torsion=0.7 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams8 = axial_flexural_critical_load(
    profile=small_channel,
    length_major_axis=1.4 * m,
    length_minor_axis=1.4 * m,
    length_torsion=1.4 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams9 = axial_flexural_critical_load(
    profile=small_channel,
    length_major_axis=1.205 * m,
    length_minor_axis=1.205 * m,
    length_torsion=1.205 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams10 = axial_flexural_critical_load(
    profile=small_channel,
    length_major_axis=0.675 * m,
    length_minor_axis=0.675 * m,
    length_torsion=0.675 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams11 = axial_flexural_critical_load(
    profile=small_channel,
    length_major_axis=0.428 * m,
    length_minor_axis=0.428 * m,
    length_torsion=0.428 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams12 = axial_flexural_critical_load(
    profile=small_channel,
    length_major_axis=0.152 * m,
    length_minor_axis=0.152 * m,
    length_torsion=0.152 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams = [
    beams1,
    beams2,
    beams3,
    beams4,
    beams5,
    beams6,
    beams7,
    beams8,
    beams9,
    beams10,
    beams11,
]


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
    length_minor_axis=1.4 * m,
    length_torsion=1.4 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams3data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=1.205 * m,
    length_torsion=1.205 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams4data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=0.675 * m,
    length_torsion=0.675 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams5data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=0.428 * m,
    length_minor_axis=0.428 * m,
    length_torsion=0.428 * m,
    k_factor_major_axis=2,
    k_factor_minor_axis=2,
    k_factor_torsion=2,
)

beams6data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=0.152 * m,
    length_minor_axis=0.152 * m,
    length_torsion=0.152 * m,
    k_factor_major_axis=2,
    k_factor_minor_axis=2,
    k_factor_torsion=2,
)
beams7data = AxialFlexuralCombination(
    profile=big_channel,
    length_major_axis=1.4 * m,
    length_minor_axis=0.7 * m,
    length_torsion=0.7 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams8data = AxialFlexuralCombination(
    profile=small_channel,
    length_major_axis=1.4 * m,
    length_minor_axis=1.4 * m,
    length_torsion=1.4 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams9data = AxialFlexuralCombination(
    profile=small_channel,
    length_major_axis=1.205 * m,
    length_minor_axis=1.205 * m,
    length_torsion=1.205 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams10data = AxialFlexuralCombination(
    profile=small_channel,
    length_major_axis=0.675 * m,
    length_minor_axis=0.675 * m,
    length_torsion=0.675 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams11data = AxialFlexuralCombination(
    profile=small_channel,
    length_major_axis=0.428 * m,
    length_minor_axis=0.428 * m,
    length_torsion=0.428 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams12data = AxialFlexuralCombination(
    profile=small_channel,
    length_major_axis=0.152 * m,
    length_minor_axis=0.152 * m,
    length_torsion=0.152 * m,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams_data = [
    beams1data,
    beams2data,
    beams3data,
    beams4data,
    beams5data,
    beams6data,
    beams7data,
    beams8data,
    beams9data,
    beams10data,
    beams11data,
]

critical_strengths: dict[str, DesignStrength] = {
    f"{PREFIX}{i+1}": beam.result for i, beam in enumerate(beams_data)
}

index_tuples = [
    (f"{PREFIX}{i+1}", result)
    for i, _ in enumerate(beams_data)
    for result in (FX, MY, MZ)
]
str_values = [
    beam[result] for i, beam in enumerate(beams) for result in (FX, MY, MZ)
]
data = [[value] for value in str_values]
index = pd.MultiIndex.from_tuples(index_tuples, names=["beam", "str"])
dct = {key: [value] for key, value in zip(index_tuples, str_values)}
strs = pd.DataFrame(data=[str_values], columns=index)

critical_loads = {f"{PREFIX}{i+1}": beam for i, beam in enumerate(beams)}

# directories = [
#     Path(
#         r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS\MECH"
#     ),
#     Path(
#         r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS-1\MECH"
#     ),
#     Path(
#         r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip_files\dp0\SYS-3\MECH"
#     ),
# ]

ACC_VERT = "acc_vert"


base_load_cases = {
    "vert": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2_files\dp0\SYS\MECH"
    ),
    "trans": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2_files\dp0\SYS-1\MECH"
    ),
    "long": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2_files\dp0\SYS-3\MECH"
    ),
    "wind_x": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2_files\dp0\SYS-5\MECH"
    ),
    "wind_y": Path(
        r"C:\Users\U3ZO\OneDrive - PETROBRAS\Documentos\PROJE\PROJE101\Ansys\wip2_files\dp0\SYS-6\MECH"
    ),
}

df = get_and_process_results(
    n_named_selection=11,
    load_cases=base_load_cases,
    nodes_path=base_load_cases["vert"],
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
            ("wind_x", -1.0),
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
            ("wind_x", -1.0),
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
            ("wind_y", -1.0),
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
            ("wind_y", -1.0),
        ),
    ),
]

# df = add_load_cases(df=df, load_cases=comb_load_cases)
# df = check_multiple_load_case_combined_compression_and_flexure(
#     df, list(str(i) for i in range(1, 9)), critical_loads
# ).sort_values(["beam", "h1_criteria_max"], ascending=False)
#
# res_beams1 = df.loc[df["beam"] == "beams1"]
# res_beams2 = df.loc[df["beam"] == "beams2"]
# res_beams3 = df.loc[df["beam"] == "beams3"]
# res_beams4 = df.loc[df["beam"] == "beams4"]
# res_beams5 = df.loc[df["beam"] == "beams5"]
# res_beams6 = df.loc[df["beam"] == "beams6"]
# res_beams7 = df.loc[df["beam"] == "beams7"]
# res_beams8 = df.loc[df["beam"] == "beams8"]
# res_beams9 = df.loc[df["beam"] == "beams9"]
# res_beams10 = df.loc[df["beam"] == "beams10"]
# res_beams11 = df.loc[df["beam"] == "beams11"]
#
# beams3_strs = critical_strengths["beams3"]
#
# h1_criteria = [f"h1_criteria_{name}" for name in range(1, 9)]
#
#
# def get_h1(df: pd.DataFrame) -> pd.DataFrame:
#     new_df = pd.DataFrame()
#     return df[h1_criteria]
#
#
# beam_res = [
#     res_beams1,
#     res_beams2,
#     res_beams3,
#     res_beams4,
#     res_beams5,
#     res_beams6,
#     res_beams7,
#     res_beams8,
#     res_beams9,
#     res_beams10,
#     res_beams11,
# ]
#
# h1_beams_res = [get_h1(res) for res in beam_res]
