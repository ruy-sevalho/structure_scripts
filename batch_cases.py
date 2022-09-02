from functools import partial
from typing import Collection, NamedTuple
from pathlib import Path
from typing import TextIO
import re
import os
import numpy as np
import pandas as pd
from quantities import Quantity, GPa, MPa, m, mm, cm, UnitQuantity, N
from aisc360_10.elements import (
    BeamCompressionFlexureDoublySymmetricEffectiveLength,
    DoublySymmetricIUserDefined, IsoTropicMaterial, DoublySymmetricIDimensionsUserDefined, GenericAreaProperties
)

DIRECTIONS = ("x", "y", "z")
DIRECTIONS_SUM = ("x", "y", "z", "sum")

node_reactions_header_pattern = re.compile("    NODE       FX           FY           FZ")
node_displacements_header_pattern = re.compile("    NODE       UX           UY           UZ           USUM  ")
empty_line_pattern = re.compile(" ^[ \t\n]*$")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")


def convert_to_newton(string: str):
    return Quantity(float(string) / 1000, kN)


def convert_to_mm(string: str):
    return Quantity(float(string), mm)


def process_line(line: str, non_zero_reactions: tuple[bool, bool, bool]) -> dict[int, list[str]]:
    l = line.split()
    for i, direction in enumerate(non_zero_reactions):
        if not direction:
            l.insert(i + 1, "0")  # position 0 is node index
    return {int(l[0]): [convert_to_newton(string) for string in l[1:]]}


def process_line_reaction_df(line: str, non_zero_reactions: tuple[bool, bool, bool]) -> pd.DataFrame:
    l = line.split()
    for i, direction in enumerate(non_zero_reactions):
        if not direction:
            l.insert(i + 1, "0")  # position 0 is node index
    reactions = {f"R{direction.upper()}": convert_to_newton(string) for direction, string in zip(DIRECTIONS, l[1:])}
    return pd.DataFrame({"NODE": [int(l[0])], **reactions})


def process_line_displacement_df(line: str) -> pd.DataFrame:
    l = line.split()
    displacements = {
        f"U{direction.upper()}": [convert_to_newton(string)] for direction, string in zip(DIRECTIONS_SUM, l[1:])
    }
    return pd.DataFrame({"NODE": [int(l[0])], **displacements})


def read_file(f: TextIO, non_zero_reactions: tuple[bool, bool, bool]):
    reactions_data = False
    data = dict()
    for line in f:
        if reactions_data and not line.split():
            reactions_data = False
        if reactions_data:
            data.update(process_line(line, non_zero_reactions))
        if node_reactions_header_pattern.search(line):
            reactions_data = True
    return data


def read_file_df(f: TextIO, non_zero_reactions: tuple[bool, bool, bool]):
    path_folder = Path("processed_results/")
    reactions_data = False
    displacements_data = False
    reactions = ""
    displacements = ""
    data = pd.DataFrame()
    for line in f:
        if reactions_data and not line.split():
            reactions_data = False
        if reactions_data:
            reactions += line
            # data.update(process_line_reaction_df(line, non_zero_reactions))
        if node_reactions_header_pattern.search(line):
            reactions_data = True

        if displacements_data and not line.split():
            displacements_data = False
        if displacements_data:
            displacements += line
            # data.update(process_line_displacement_df(line))
        if node_displacements_header_pattern.search(line):
            reactions_data = True
    # with open(path_folder / )
    return data


def read_results(folder_path: Path, non_zero_reactions: tuple[bool, bool, bool] = (1, 1, 1)):
    results = dict()
    for i, file in enumerate(os.listdir(folder_path)):
        with open(folder_path / file, 'r') as f:
            results.update({f"{file[:-4]}": read_file(f, non_zero_reactions)})
    return results


def read_results_df(folder_path: Path, non_zero_reactions: tuple[bool, bool, bool] = (1, 1, 1)):
    results = pd.DataFrame()
    for i, file in enumerate(os.listdir(folder_path)):
        with open(folder_path / file, 'r') as f:
            current_result = pd.concat(
                (pd.DataFrame({"CASE": [f"{file[:-4]}"]}), read_file_df(f, non_zero_reactions))
            )
            results = pd.concat(())
            # results.update({f"{file[:-4]}": read_file(f, non_zero_reactions)})
    return results


# def read_results_df(folder_path: Path):
#     results = dict()
#     for i, file in enumerate(os.listdir(folder_path)):
#         with open(folder_path / file, 'r') as f:
#             results.update({f"{file[:-4]}": read_file(f)})
#     return results


class ReactionsForces(NamedTuple):
    x: Quantity = Quantity(0, 'N')
    y: Quantity = Quantity(0, 'N')
    z: Quantity = Quantity(0, 'N')


class ForcesAndMoments(NamedTuple):
    fx: Quantity = Quantity(0, 'N')
    fy: Quantity = Quantity(0, 'N')
    fz: Quantity = Quantity(0, 'N')
    mx: Quantity = Quantity(0, 'N*m')
    my: Quantity = Quantity(0, 'N*m')
    mz: Quantity = Quantity(0, 'N*m')


class ReactionAtBase(NamedTuple):
    required_axial_strength: Quantity = Quantity(0, "N")
    required_moment_x: Quantity = Quantity(0, "N*m")
    required_moment_y: Quantity = Quantity(0, "N*m")
    required_moment_z: Quantity = Quantity(0, "N*m")


def reaction_per_column(
        reactions_1: ReactionsForces,
        reactions_2: ReactionsForces,
        dy: Quantity = Quantity(.65, "m"),
):
    for reaction_1, reaction_2 in zip(reactions_1, reactions_2):
        pass
    forces = (
        reaction_1 + reaction_2 for reaction_1, reaction_2 in zip(reactions_1, reactions_2)
    )
    moment_x = (reactions_1.z - reactions_2.z) * dy
    moment_z = (reactions_2.x - reactions_2.y) * dy
    return ForcesAndMoments(
        *forces,
        mx=moment_x,
        mz=moment_z
    )


def reaction_at_base(reaction: ForcesAndMoments, length: Quantity):
    return ReactionAtBase(
        required_axial_strength=reaction.fz,
        required_moment_x=reaction.mx + reaction.fy * length,
        required_moment_y=reaction.my + reaction.fx * length
    )


#
# def process_reactions_input(
#         df: pd.DataFrame,
#         n_comb: int = 7,
#         number_columns: int = 3,
#         dy=Quantity(.65, "m"),
#         length=Quantity(5.60, "m")
# ):
#     limit = n_comb * number_columns
#     df1, df2 = df[0:limit], df[limit:]
#     df = pd.DataFrame()
#     for row_1, row_2 in zip(df1, df2):
#         row = reaction_per_column(
#             row_1[-3:],
#             row_2[-3:]
#         )
#         df = pd.concat(
#             pd.DataFrame(
#                 {
#                     "Rx"
#                 }
#             )
#         )
#     return


def several_loads_results(
        profile: DoublySymmetricIUserDefined,
        unbraced_length: Quantity,
        loads: Collection[tuple[Quantity, Quantity, Quantity]],
        factor_k_minor_axis: float = 1.0,
        factor_k_major_axis: float = 1.0,
        factor_k_torsion: float = 1.0,
        reactions_info: pd.DataFrame = pd.DataFrame()

):
    partial_beam = partial(
        BeamCompressionFlexureDoublySymmetricEffectiveLength,
        profile=profile,
        unbraced_length=unbraced_length,
        factor_k_torsion=factor_k_torsion,
        factor_k_major_axis=factor_k_major_axis,
        factor_k_minor_axis=factor_k_minor_axis
    )
    results_df = pd.DataFrame()
    for load in loads:
        beam: BeamCompressionFlexureDoublySymmetricEffectiveLength = partial_beam(
            required_axial_strength=load[0],
            required_major_axis_flexure_strength=load[1].rescale(kN * m),
            required_minor_axis_flexure_strength=load[2].rescale(kN * m),
        )
        results_df = pd.concat((results_df, beam.results_h1_df))
    if not reactions_info.empty:
        results_df = pd.concat((reactions_info, results_df), axis=1)
    return results_df


def process_results(
        reactions_path: Path,
        column_end_node_pairs: tuple[tuple[int, int], tuple[int, int], tuple[int, int]],
        length: Quantity,
        non_zero_reactions: tuple[bool, bool, bool] = (True, True, True)
):
    reactions_at_node_per_case = read_results(reactions_path, non_zero_reactions)
    reactions_at_column_end: dict[str, dict[str, ForcesAndMoments]] = dict()
    for key, value in reactions_at_node_per_case.items():
        reactions_at_column_end.update(
            {
                key: {
                    f"coluna_{i}":
                        reaction_per_column(
                            ReactionsForces(*value[node[0]]),
                            ReactionsForces(*value[node[1]])
                        )
                    for i, node in enumerate(column_end_node_pairs)
                }
            }
        )
    reactions_base = [
        reaction_at_base(reaction=value, length=length)
        for value_parent in reactions_at_column_end.values() for value in value_parent.values()
    ]
    reactions_info_df = pd.DataFrame()
    for key_parent, value_parent in reactions_at_column_end.items():
        for key, value in value_parent.items():
            current_reaction = pd.DataFrame(
                {
                    "caso": [key_parent],
                    "coluna": [key],
                    "rx": [value.fx],
                    "ry": [value.fy],
                    'rz': [value.fz],
                    "mx": [value.mx],
                }
            )
            reactions_info_df = pd.concat(
                (reactions_info_df, current_reaction)
            )

    reactions_data = {
        f"{key_parent}_{key}"
        for key_parent, value_parent in reactions_at_column_end.items() for key in value_parent
    }
    return reactions_base, reactions_info_df


def convert_to_mm_(value):
    return Quantity(value, mm)

def convert_to_mag(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame()


if __name__ == "__main__":
    # df = pd.read_fwf("displacements.txt", )
    # df = df.fillna(0.)
    # df.applymap()
    # df.UX = [convert_to_mm_(value) for value in df.UX]
    # dft = df.transform(lambda x: Quantity(x, mm))
    # # for value in dft.UX:
    # #     print(value.rescale("cm"))
    steel = IsoTropicMaterial(
        modulus_linear=200 * GPa,
        modulus_shear=77 * GPa,
        poisson_ratio=0.3,
        yield_stress=355 * MPa
    )
    area_properties_wx250x250x73 = GenericAreaProperties(
        area=94.90 * cm ** 2,
        minor_axis_inertia=3883 * cm ** 4,
        minor_axis_elastic_section_modulus=306 * cm ** 3,
        minor_axis_plastic_section_modulus=463 * cm ** 3,
        major_axis_inertia=11508 * cm ** 4,
        major_axis_elastic_section_modulus=910 * cm ** 3,
        major_axis_plastic_section_modulus=1007 * cm ** 3,
        major_axis_radius_of_gyration=11 * cm,
        torsional_constant=66 * cm ** 4,
        warping_constant=544000 * cm ** 6
    )
    dimensions_wx250x250x73 = DoublySymmetricIDimensionsUserDefined(
        flange_width=254 * mm,
        flange_thickness=14.2 * mm,
        web_thickness=8.6 * mm,
        total_height=254 * mm
    )
    profile_wx250x250x73 = DoublySymmetricIUserDefined(
        area_properties=area_properties_wx250x250x73,
        dimensions=dimensions_wx250x250x73,
        material=steel
    )
    # case_names = ("reactions1530", "reactions1030")
    # reactions_path = "reactions_report"
    # column_end_node_pairs = ((790, 344), (587, 552), (845, 820))
    length = Quantity(3.3, m)
    results = dict()
    analysis = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_wx250x250x73,
        unbraced_length=length,
        required_axial_strength=2.3557e+005*N + 29*kN,
        required_major_axis_flexure_strength=3.7063e+007*N*mm,
    )
    report = analysis.latex.resume_latex
    loads_1 = (
        (152360 * N, 46253000 * N * mm, 1037300 * N * mm),
        (175940 * N, 41498000 * N * mm, 788910 * N * mm),
        (180730 * N, 34337000 * N * mm, 1150700 * N * mm),
        (151200 * N, 39471000 * N * mm, 1394000 * N * mm),
        (141290 * N, 41952000 * N * mm, 291570 * N * mm),
        (142040 * N, 41892000 * N * mm, 230530 * N * mm),
        (141640 * N, 41203000 * N * mm, 186190 * N * mm),

    )
    loads_2 = (
        (231500 * N, 43419000 * N * mm, 1141600 * N * mm),
        (225080 * N, 44568000 * N * mm, 1131500 * N * mm),
        (246730 * N, 39703000 * N * mm, 1544800 * N * mm),
        (274300 * N, 34404000 * N * mm, 1548500 * N * mm),
        (229440 * N, 41279000 * N * mm, 404740 * N * mm),
        (228260 * N, 42354000 * N * mm, 291740 * N * mm),
        (227500 * N, 42143000 * N * mm, 30151 * N * mm),

    )
    loads_3 = (
        (196200 * N, 42524000 * N * mm, 664980 * N * mm),
        (195410 * N, 43004000 * N * mm, 667550 * N * mm),
        (197320 * N, 44254000 * N * mm, 626760 * N * mm),
        (199420 * N, 43503000 * N * mm, 681980 * N * mm),
        (250870 * N, 33378000 * N * mm, 522580 * N * mm),
        (239230 * N, 43868000 * N * mm, 632150 * N * mm),
        (222390 * N, 46431000 * N * mm, 846790 * N * mm),

    )
    mult_cases_1 = several_loads_results(
        profile=profile_wx250x250x73,
        unbraced_length=length,
        loads=loads_1
    )
    mult_cases_2 = several_loads_results(
        profile=profile_wx250x250x73,
        unbraced_length=length,
        loads=loads_2
    )
    mult_cases_3 = several_loads_results(
        profile=profile_wx250x250x73,
        unbraced_length=length,
        loads=loads_3
    )
    mult_cases_1.to_excel("mult_cases_c1.xlsx")
    mult_cases_2.to_excel("mult_cases_c2.xlsx")
    mult_cases_3.to_excel("mult_cases_c3.xlsx")
    with open('carga_critica.tex', 'w') as f:
        f.write(report)
    print(analysis.compression.design_strength.rescale(kN))
    print(analysis.flexure.design_strength_major_axis.rescale(kN * m))
    print(analysis.flexure.design_strength_minor_axis.rescale(kN * m))
    print(analysis.compression_flexure_combined_criteria_h1_1)
    # result_generator = partial(
    #     several_loads_results,
    #     profile=profile_wx250x250x73,
    #     unbraced_length=length/2,
    # )
    # for reaction_path, case_name in zip(reactions_path, case_names):
    #     reactions_base, reactions_names = process_results(reaction_path, column_end_node_pairs)
    #     result_case = result_generator(
    #         loads=reactions_base,
    #         names=reactions_names
    #     )
    #     results.update({case_name: result_case})
    # reactions_base, reactions_info_df = process_results(
    #     Path("reactions_report/"),
    #     column_end_node_pairs,
    #     length=length,
    #     non_zero_reactions=(False, False, True)
    # )
    # results_report: pd.DataFrame = result_generator(
    #     loads=reactions_base,
    #     reactions_info=reactions_info_df
    # )
    #
    # results_report.to_excel("results_report.xlsx")

    # reactions_base, reactions_info_df = process_results(
    #     Path("reactions1030/"),
    #     column_end_node_pairs
    # )
    # results1030 = result_generator(
    #     loads=reactions_base,
    #     names=reactions_names
    # ).sort_values("h1_criteria", ascending=False)
    # reactions_base, reactions_names, reactions_at_column_end_530 = process_results(
    #     Path("reactions530/"),
    #     column_end_node_pairs
    # )
    # results530 = result_generator(
    #     loads=reactions_base,
    #     names=reactions_names
    # ).sort_values("h1_criteria", ascending=False)
    # reactions_base, reactions_names, reactions_at_column_end_430 = process_results(
    #     Path("reactions430/"),
    #     column_end_node_pairs
    # )
    # results430 = result_generator(
    #     loads=reactions_base,
    #     names=reactions_names
    # ).sort_values("h1_criteria", ascending=False)
