# Module for calculating beam in accordance to ANSI/AISC 360-10
# Author: Ruy Sevalho Goncalves


from quantities import Quantity, dimensionless, cm, UnitQuantity, m, mm, GPa, MPa, N

from elements import IsoTropicMaterial, DoublySymmetricIUserDefined, \
    BeamCompressionFlexureDoublySymmetricEffectiveLength, DoublySymmetricIDimensionsUserDefined, GenericAreaProperties, \
    SectionProfile, BeamCompressionEffectiveLength, BeamFlexureDoublySymmetric, Material
from latex import _dataframe_table_columns
from helpers import Slenderness, ConstructionType

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilonewton", 1000 * N, symbol="kN")
LATEX_ABREVIATION = 'latex'


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
    # print(area_properties_w_arbitrary.table_keys())
    # print(area_properties_w_arbitrary.as_table())
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
    table_str = _dataframe_table_columns(
        profile_wx250x250x73_calculated.area_properties.table(
            filter_names=["torsional_constant", "torsional_radius_of_gyration", "warping_constant"]
        ),
        unit_display="cell",
        include_description=True
    )
    with open("section_tables.tex", "w") as f:
        table_str.dump(f)
    print(table_str.dumps())
    profile_arbitrary = DoublySymmetricIUserDefined(
        dimensions=dimensions_w_arbitrary,
        material=steel
    )
    beam_length = 2.60 * m
    beam_combined_10 = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_arbitrary,
        unbraced_length=beam_length
    )
    beam_combined_14 = BeamCompressionFlexureDoublySymmetricEffectiveLength(
        profile=profile_wx250x250x73,
        unbraced_length=beam_length
    )
    required_axial_strength = 60 * kN
    required_major_axis_strength = 120 * kN * m
    required_minor_axis_strength = 0 * kN * m
    # print(profile_wx250x250x73.warping_constant.rescale(dm ** 6))
    # print(profile_wx250x250x73.dimensions.distance_between_centroids.rescale(mm))
    # print(profile_wx250x250x73.slenderness.flange_axial_limit_ratio)
    # print(profile_wx250x250x73.slenderness.flange_ratio)
    # print(profile_wx250x250x73.slenderness.web_axial_compression_limit_ratio)
    # print(profile_wx250x250x73.slenderness.web_ratio)
    # print(profile_wx250x250x73.area_properties.minor_axis_radius_of_gyration)
    # print("compression")
    # print(beam_compression.minor_axis_slenderness)
    # print((4.71 * (steel.modulus_linear / steel.yield_stress) ** 0.5).simplified)
    # print(beam_compression.elastic_flexural_buckling_stress)
    # print(beam_compression.flexural_buckling_critical_stress)
    # print(beam_compression.strength_flexural_buckling.rescale(kN))
    # print('flexure')
    # print(profile_wx250x250x73.slenderness.flange_flexural_compact_limit_ratio)
    # print(profile_wx250x250x73.slenderness.web_flexural_compact_limit_ratio)
    # print(beam_flexure.strength_major_axis_yield.rescale(kN * m))
    # print(profile_wx250x250x73.limit_length_yield.rescale(m))
    # print(profile_wx250x250x73.limit_length_torsional_buckling.rescale(m))
    # print(profile_wx250x250x73.warping_constant.rescale(cm ** 6))
    # print(profile_wx250x250x73.effective_radius_of_gyration.rescale(mm))

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


def print_obj_pairs_attributes(pair: tuple, attributes):
    for attribute in attributes:
        attrs = [getattr(obj, attribute) for obj in pair]
        print(f"{attribute}_1: {attrs[0]}")
        print(f"{attribute}_2: {attrs[1]}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    beam_10, beam_14 = main()
    # attrs = ('area', "minor_axis_inertia", "minor_axis_radius_of_gyration", "minor_axis_elastic_section_modulus",
    #          "minor_axis_plastic_section_modulus", "major_axis_inertia", "major_axis_radius_of_gyration",
    #          "major_axis_elastic_section_modulus",
    #          "major_axis_plastic_section_modulus", "torsional_constant")
    # print_obj_pairs_attributes((user_defined.area_properties, calculated.area_properties), attrs)
