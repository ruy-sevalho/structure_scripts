from functools import partial
from typing import Collection
import pandas as pd
from quantities import Quantity, GPa, MPa, m, mm, cm, UnitQuantity, N
from structure_scripts.aisc_360_10.elements import (
    BeamCompressionFlexureDoublySymmetricEffectiveLength,
)
from structure_scripts.aisc_360_10.i_profile import (
    DoublySymmetricIDimensionsUserDefined,
    DoublySymmetricIAISC36010,
)
from structure_scripts.materials import (
    IsotropicIsotropicMaterialUserDefined,
)
from structure_scripts.sections import DirectInputAreaProperties

kN = UnitQuantity("kN", 1000 * N)


def several_loads_results(
    profile: DoublySymmetricIAISC36010,
    unbraced_length: Quantity,
    loads: Collection[tuple[Quantity, Quantity, Quantity]],
    factor_k_minor_axis: float = 1.0,
    factor_k_major_axis: float = 1.0,
    factor_k_torsion: float = 1.0,
    reactions_info: pd.DataFrame = pd.DataFrame(),
):
    partial_beam = partial(
        BeamCompressionFlexureDoublySymmetricEffectiveLength,
        profile=profile,
        unbraced_length_major_axis=unbraced_length,
        factor_k_torsion=factor_k_torsion,
        factor_k_major_axis=factor_k_major_axis,
        factor_k_minor_axis=factor_k_minor_axis,
    )
    results_df = pd.DataFrame()
    for load in loads:
        beam: BeamCompressionFlexureDoublySymmetricEffectiveLength = (
            partial_beam(
                required_axial_strength=load[0].rescale(kN),
                required_major_axis_flexural_strength=load[1].rescale(kN * m),
                required_minor_axis_flexural_strength=load[2].rescale(kN * m),
            )
        )
        results_df = pd.concat((results_df, beam.results_h1_df))
    if not reactions_info.empty:
        results_df = pd.concat((reactions_info, results_df), axis=1)
    return results_df


if __name__ == "__main__":
    steel = IsotropicIsotropicMaterialUserDefined(
        modulus_linear=200 * GPa,
        modulus_shear=77 * GPa,
        poisson_ratio=0.3,
        yield_stress=355 * MPa,
    )
    area_properties_wx250x250x73 = DirectInputAreaProperties(
        area=94.90 * cm**2,
        minor_axis_inertia=3883 * cm**4,
        minor_axis_elastic_section_modulus=306 * cm**3,
        minor_axis_plastic_section_modulus=463 * cm**3,
        major_axis_inertia=11508 * cm**4,
        major_axis_elastic_section_modulus=910 * cm**3,
        major_axis_plastic_section_modulus=1007 * cm**3,
        major_axis_radius_of_gyration=11 * cm,
        polar_inertia=66 * cm**4,
        warping_constant=544000 * cm**6,
    )
    dimensions_wx250x250x73 = DoublySymmetricIDimensionsUserDefined(
        flange_width=254 * mm,
        flange_thickness=14.2 * mm,
        web_thickness=8.6 * mm,
        total_height=254 * mm,
    )
    profile_wx250x250x73 = DoublySymmetricIAISC36010(
        area_properties=area_properties_wx250x250x73,
        dimensions=dimensions_wx250x250x73,
        material=steel,
    )
    length = Quantity(3.3, m)
    analysis = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_wx250x250x73,
        unbraced_length_major_axis=length,
        required_axial_strength=2.3557e005 * N + 29 * kN,
        required_major_axis_flexural_strength=3.7063e007 * N * mm,
    )
    # report = analysis.latex.resume_latex
    loads_1 = (
        (129230 * N, 38937000 * N * mm, -132770 * N * mm),
        (189210 * N, 30492000 * N * mm, 482170 * N * mm),
        (165910 * N, 39899000 * N * mm, 778010 * N * mm),
        (132140 * N, 49685000 * N * mm, 1580900 * N * mm),
        (126760 * N, 47064000 * N * mm, 1489800 * N * mm),
        (125670 * N, 41909000 * N * mm, -257080 * N * mm),
        (126990 * N, 41675000 * N * mm, -258800 * N * mm),
        (126270 * N, 41520000 * N * mm, 113050 * N * mm),
    )
    loads_2 = (
        (268870 * N, 31992000 * N * mm, -181880 * N * mm),
        (217290 * N, 44618000 * N * mm, 1051100 * N * mm),
        (223720 * N, 43941000 * N * mm, 1119800 * N * mm),
        (234750 * N, 43228000 * N * mm, 1548100 * N * mm),
        (240140 * N, 45550000 * N * mm, 1500600 * N * mm),
        (230590 * N, 42322000 * N * mm, 361480 * N * mm),
        (228900 * N, 42171000 * N * mm, 371700 * N * mm),
        (227960 * N, 40917000 * N * mm, -192030 * N * mm),
    )
    loads_3 = (
        (203750 * N, 39622000 * N * mm, -763890 * N * mm),
        (196310 * N, 43433000 * N * mm, 281770 * N * mm),
        (195960 * N, 43231000 * N * mm, 324080 * N * mm),
        (195640 * N, 44367000 * N * mm, 733750 * N * mm),
        (198190 * N, 45836000 * N * mm, 690980 * N * mm),
        (219390 * N, 50249000 * N * mm, -460510 * N * mm),
        (233520 * N, 47305000 * N * mm, -371070 * N * mm),
        (247170 * N, 33399000 * N * mm, -580560 * N * mm),
    )
    mult_cases_1 = several_loads_results(
        profile=profile_wx250x250x73, unbraced_length=length, loads=loads_1
    )
    mult_cases_2 = several_loads_results(
        profile=profile_wx250x250x73, unbraced_length=length, loads=loads_2
    )
    mult_cases_3 = several_loads_results(
        profile=profile_wx250x250x73, unbraced_length=length, loads=loads_3
    )
    mult_cases_1.to_excel("mult_cases_c1.xlsx")
    mult_cases_2.to_excel("mult_cases_c2.xlsx")
    mult_cases_3.to_excel("mult_cases_c3.xlsx")
    # with open('carga_critica.tex', 'w') as f:
    #     f.write(report)
