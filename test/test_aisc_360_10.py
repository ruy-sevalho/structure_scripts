from structure_scripts.aisc_360_10.i_profile import (
    DoublySymmetricI,
    DoublySymmetricIDimensions,
)
from structure_scripts.sections import section_geo_properties
from structure_scripts.materials import steel355mpa
from quantities import Quantity, cm, m, mm

section_properties_127x76x13 = section_geo_properties(
    area=16.5 * cm**2,
    major_axis_inertia=473 * cm**4,
    minor_axis_inertia=56 * cm**4,
    minor_axis_elastic_section_modulus=15 * cm**3,
    major_axis_elastic_section_modulus=75 * cm**3,
    major_axis_plastic_section_modulus=84 * cm**3,
    polar_inertia=2.85 * cm**4,
    warping_constant=2000000000 * mm**6,
)
dimensions_127x76x13 = DoublySymmetricIDimensions(
    flange_width=76 * mm,
    flange_thickness=7.6 * mm,
    web_thickness=4 * mm,
    web_radii=7.6 * mm,
    total_height=127 * mm,
)
w_127x127x73x13 = DoublySymmetricI(
    dimensions=dimensions_127x76x13,
    material=steel355mpa,
    geo_properties=section_properties_127x76x13,
)
w_127x127x73x13_calculated_geo_properties = DoublySymmetricI(
    dimensions=dimensions_127x76x13,
    material=steel355mpa,
)


def test_double_symmetric_i_accepts_area_properties():
    assert w_127x127x73x13.geo_properties == section_properties_127x76x13


def test_double_symmetric_i_no_area_properties():
    assert w_127x127x73x13_calculated_geo_properties.geo_properties