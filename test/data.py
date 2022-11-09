from quantities import cm, mm, m

from structure_scripts.aisc_360_10.compression import BeamCompression
from structure_scripts.sections import (
    create_doubly_symmetric_i, SectionChecks,
)
from structure_scripts.materials import steel355mpa
from structure_scripts.sections import DoublySymmetricIDimensions
from structure_scripts.section_properties import section_geo_properties

area_properties_creator = section_geo_properties
doubly_symmetric_i_creator = create_doubly_symmetric_i
doubly_symmetric_i_dimensions_creator = DoublySymmetricIDimensions
section_properties_wrong = area_properties_creator(
    area=1 * cm**2,
    major_axis_inertia=1 * cm**4,
    minor_axis_inertia=1 * cm**4,
    minor_axis_elastic_section_modulus=1 * cm**3,
    major_axis_elastic_section_modulus=1 * cm**3,
    major_axis_plastic_section_modulus=14 * cm**3,
    polar_inertia=1 * cm**4,
    warping_constant=1 * mm**6,
)
dimensions_wrong = doubly_symmetric_i_dimensions_creator(
    flange_width=1 * mm,
    flange_thickness=1 * mm,
    web_thickness=1 * mm,
    web_radii=1 * mm,
    total_height=1 * mm,
)
wrong_section = doubly_symmetric_i_creator(
    dimensions=dimensions_wrong,
    material=steel355mpa,
    area_properties=section_properties_wrong,
)
section_properties_127x76x13 = area_properties_creator(
    area=16.5 * cm**2,
    major_axis_inertia=473 * cm**4,
    minor_axis_inertia=56 * cm**4,
    minor_axis_elastic_section_modulus=15 * cm**3,
    major_axis_elastic_section_modulus=75 * cm**3,
    major_axis_plastic_section_modulus=84 * cm**3,
    polar_inertia=2.85 * cm**4,
    warping_constant=2000000000 * mm**6,
)
dimensions_127x76x13 = doubly_symmetric_i_dimensions_creator(
    flange_width=76 * mm,
    flange_thickness=7.6 * mm,
    web_thickness=4 * mm,
    web_radii=7.6 * mm,
    total_height=127 * mm,
)
w_127x127x73x13 = doubly_symmetric_i_creator(
    dimensions=dimensions_wrong,
    material=steel355mpa,
    area_properties=section_properties_127x76x13,
)
dimensions_200x10_200x10 = doubly_symmetric_i_dimensions_creator(
    flange_width=200 * mm,
    flange_thickness=10 * mm,
    web_thickness=10 * mm,
    total_height=220 * mm,
)
w_200x10_200x10 = doubly_symmetric_i_creator(
    dimensions=dimensions_200x10_200x10, material=steel355mpa
)
sections: dict[str, SectionChecks] = {
    "wrong_section": wrong_section,
    "w_127x127x73x13": w_127x127x73x13,
    "w_200x10_200x10": w_200x10_200x10,
}
beam_params = {
    "beam_01": BeamCompression(length_major_axis=1 * m),
    "beam_02": BeamCompression(length_major_axis=2 * m),
    "beam_04": BeamCompression(length_major_axis=4 * m),
}
