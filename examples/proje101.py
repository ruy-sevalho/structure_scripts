from pathlib import Path

from quantities import Quantity, m

from structure_scripts.aisc_360_10.aisc_database import AISC_Sections
from structure_scripts.aisc_360_10.channel import ChannelAISC36010
from structure_scripts.aisc_360_10.i_section import DoublySymmetricIAISC36010
from structure_scripts.aisc_360_10.sections import (
    ConstructionType,
    axial_flexural_critical_load,
)
from structure_scripts.ansys import (
    get_and_process_results,
)
from structure_scripts.load_combination import (
    add_load_case,
    add_load_cases,
    check_load_case_combined_compression_and_flexure,
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
    length_torsion=distance_between_columns_x,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)

beams3 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=1.205 * m,
    length_torsion=distance_between_columns_x,
    k_factor_major_axis=1,
    k_factor_minor_axis=1,
    k_factor_torsion=1,
)
beams4 = axial_flexural_critical_load(
    profile=big_channel,
    length_major_axis=distance_between_columns_x,
    length_minor_axis=0.675 * m,
    length_torsion=distance_between_columns_x,
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
    length_torsion=1.4 * m,
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

critical_loads = {f"{PREFIX}{i+1}": beam for i, beam in enumerate(beams)}

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
    n_named_selection=11,
    load_cases=base_load_cases,
    nodes_path=base_load_cases["vert"],
)
comb_load_cases = [
    ("1", (("vert", 1.28000), ("trans", 0.31), ("long", 0.15))),
    ("2", (("vert", 1.28000), ("trans", -0.31), ("long", 0.15))),
]

df = add_load_cases(df=df, load_cases=comb_load_cases)
df = check_load_case_combined_compression_and_flexure(df, "1", critical_loads)
