# Module for calculating beam in accordance to ANSI/AISC 360-10
# Author: Ruy Sevalho Goncalves
from pylatex.base_classes import CommandBase
from quantities import Quantity, dimensionless, cm, UnitQuantity, m, mm, GPa, MPa, N

from aisc360_10.elements import (
    IsoTropicMaterial, DoublySymmetricIUserDefined,
    BeamCompressionFlexureDoublySymmetricEffectiveLength, DoublySymmetricIDimensionsUserDefined,
    GenericAreaProperties,
    SectionProfile, BeamCompressionEffectiveLength, BeamFlexureDoublySymmetric, Material, latex_wrapper
)
from aisc360_10.latex_helpers import (
    _dataframe_table_columns, Alpha, Frac,
    _slenderness_default_limit_ratio_latex
)
from pylatex import Quantity as plQ
from aisc360_10.helpers import Slenderness, ConstructionType

from pylatex import Command, Document

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")
LATEX_ABBREVIATION = 'latex'


def main():
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
        torsional_constant=66 * cm ** 4,
    )
    dimensions_wx250x250x73 = DoublySymmetricIDimensionsUserDefined(
        flange_width=250 * mm,
        flange_thickness=14.2 * mm,
        web_thickness=8.6 * mm,
        total_height=250 * mm
    )
    area_properties_w_arbitrary = GenericAreaProperties(
        area=5990 * mm ** 2,
        minor_axis_inertia=1270 * cm ** 4,
        minor_axis_elastic_section_modulus=127 * cm ** 3,
        minor_axis_plastic_section_modulus=195 * cm ** 3,
        major_axis_inertia=6470 * cm ** 4,
        major_axis_elastic_section_modulus=518 * cm ** 3,
        major_axis_plastic_section_modulus=584 * cm ** 3,
        torsional_constant=66 * cm ** 4,
    )
    dimensions_w_arbitrary = DoublySymmetricIDimensionsUserDefined(
        flange_width=250 * mm,
        flange_thickness=9.5 * mm,
        web_thickness=9.5 * mm,
        total_height=250 * mm
    )
    profile_wx250x250x73 = DoublySymmetricIUserDefined(
        area_properties=area_properties_wx250x250x73,
        dimensions=dimensions_wx250x250x73,
        material=steel
    )
    profile_wx250x250x73_calculated = DoublySymmetricIUserDefined(
        dimensions=dimensions_wx250x250x73,
        material=steel
    )
    profile_arbitrary = DoublySymmetricIUserDefined(
        dimensions=dimensions_w_arbitrary,
        material=steel
    )
    beam_length = 3.60 * m
    required_axial_strength = 60 * kN
    required_major_axis_strength = 120 * kN * m
    required_minor_axis_strength = 0 * kN * m
    beam_combined_10 = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_arbitrary,
        unbraced_length=beam_length,
        required_axial_strength=required_axial_strength,
        required_minor_axis_flexure_strength=required_minor_axis_strength,
        required_major_axis_flexure_strength=required_major_axis_strength
    )
    beam_combined_14 = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_wx250x250x73,
        unbraced_length=beam_length,
        required_axial_strength=required_axial_strength,
        required_minor_axis_flexure_strength=required_minor_axis_strength,
        required_major_axis_flexure_strength=required_major_axis_strength
    )
    latex_report_str = beam_combined_14.latex.stand_alone_report
    with open("latex/calculation_memory.tex", "w") as f:
        f.write(latex_report_str)
    # print("10 mm")
    # print(
    #     beam_combined_10.compression_flexure_combined_criteria_h1_1(
    #         required_axial_strength=required_axial_strength,
    #         required_major_axis_flexure_strength=required_major_axis_strength,
    #         required_minor_axis_flexure_strength=required_minor_axis_strength
    #     )
    # )
    # print("14 mm")
    # print(
    #     beam_combined_14.compression_flexure_combined_criteria_h1_1(
    #         required_axial_strength=required_axial_strength,
    #         required_major_axis_flexure_strength=required_major_axis_strength,
    #         required_minor_axis_flexure_strength=required_minor_axis_strength
    #     )
    # )
    return beam_combined_10, beam_combined_14


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    beam_10, beam_14 = main()
