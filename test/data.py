from quantities import cm, mm, m, inch

from structure_scripts.aisc_360_10.compression import BeamCompression
from structure_scripts.sections_from_dimensions import (
    create_doubly_symmetric_i,
    SectionChecks,
    create_channel,
    new_channel_dimensions,
)
from structure_scripts.materials import steel355MPa
from structure_scripts.sections_from_dimensions import (
    DoublySymmetricIDimensions,
)
from structure_scripts.section_properties import section_geo_properties

area_properties_creator = section_geo_properties
doubly_symmetric_i_creator = create_doubly_symmetric_i
doubly_symmetric_i_dimensions_creator = DoublySymmetricIDimensions
channel_dimensions_creator = new_channel_dimensions
channel_creator = create_channel

section_properties_wrong = area_properties_creator(
    area=1 * cm**2,
    major_axis_inertia=1 * cm**4,
    minor_axis_inertia=1 * cm**4,
    minor_axis_elastic_section_modulus=1 * cm**3,
    major_axis_elastic_section_modulus=1 * cm**3,
    major_axis_plastic_section_modulus=14 * cm**3,
    torsional_constant=1 * cm**4,
    warping_constant=1 * mm**6,
)
dimensions_wrong = doubly_symmetric_i_dimensions_creator(
    flange_width=1 * mm,
    flange_thickness=1 * mm,
    web_thickness=1 * mm,
    web_radii=1 * mm,
    depth=1 * mm,
)
wrong_section = doubly_symmetric_i_creator(
    dimensions=dimensions_wrong,
    material=steel355MPa,
    area_properties=section_properties_wrong,
)
section_properties_127x76x13 = area_properties_creator(
    area=16.5 * cm**2,
    major_axis_inertia=473 * cm**4,
    minor_axis_inertia=56 * cm**4,
    minor_axis_elastic_section_modulus=15 * cm**3,
    major_axis_elastic_section_modulus=75 * cm**3,
    major_axis_plastic_section_modulus=84 * cm**3,
    torsional_constant=2.85 * cm**4,
    warping_constant=2000000000 * mm**6,
)
dimensions_127x76x13 = doubly_symmetric_i_dimensions_creator(
    flange_width=76 * mm,
    flange_thickness=7.6 * mm,
    web_thickness=4 * mm,
    web_radii=7.6 * mm,
    depth=127 * mm,
)
w_127x127x73x13 = doubly_symmetric_i_creator(
    dimensions=dimensions_127x76x13,
    material=steel355MPa,
    area_properties=section_properties_127x76x13,
)
# dimensions_200x10_200x10 = doubly_symmetric_i_dimensions_creator(
#     flange_width=200 * mm,
#     flange_thickness=10 * mm,
#     web_thickness=10 * mm,
#     depth=220 * mm,
# )
# w_200x10_200x10 = doubly_symmetric_i_creator(
#     dimensions=dimensions_200x10_200x10, material=steel355mpa
# )

# dimensions_432x102_channel = new_channel_dimensions(
#     flange_thickness=16.8 * mm,
#     flange_width=101.6 * mm,
#     web_thickness=12.2 * mm,
#     channel_depth=431.8 * mm,
# )
# channel_432x102 = create_channel(
#     dimensions=dimensions_432x102_channel, material=steel355mpa
# )
# channel_6_inch_8dot2_lb_ft = channel_creator(
#     dimensions=new_channel_dimensions(
#         flange_thickness=0.343 * inch,
#         flange_width=1.920 * inch,
#         web_thickness=0.200 * inch,
#         channel_depth=6.00 * inch,
#     )
# )

sections: dict[str, SectionChecks] = {
    "wrong_section": wrong_section,
    "w_127x127x73x13": w_127x127x73x13,
    # "w_200x10_200x10": w_200x10_200x10,
    # "channel_432x102": channel_432x102,
    # "channel_6_inch_8dot2_lb_ft": channel_6_inch_8dot2_lb_ft,
}
