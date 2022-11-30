from dataclasses import asdict

from pytest import mark
from quantities import Quantity, mm

from test.data import sections
from structure_scripts.sections import AreaProperties, SectionChecks
from test.helpers import same_units_dictionary_simplify_for_test_assert

expected_area_properties = {
    "w_200x10_200x10": AreaProperties(
        area=Quantity(6000, mm**2),
        major_axis_inertia=Quantity(50800000, mm**4),
        minor_axis_inertia=Quantity(13350000, mm**4),
        torsional_constant=Quantity(203333.3333, mm**4),
        major_axis_elastic_section_modulus=Quantity(461818.1818, mm**3),
        minor_axis_elastic_section_modulus=Quantity(133500, mm**3),
        major_axis_plastic_section_modulus=Quantity(520000, mm**3),
        minor_axis_plastic_section_modulus=Quantity(205000, mm**3),
        major_axis_radius_of_gyration=Quantity(92.01449161, mm),
        minor_axis_radius_of_gyration=Quantity(47.16990566, mm),
        polar_radius_of_gyration=Quantity(103.4005158, mm),
        major_axis_shear_centroid=Quantity(0, mm),
        minor_axis_shear_centroid=Quantity(0, mm),
        warping_constant=Quantity(1.47184e11, mm**6),
    ),
    "channel_432x102": AreaProperties(
        area=Quantity(8271.8, mm**2),
        major_axis_inertia=Quantity(211256209.2, mm**4),
        minor_axis_inertia=Quantity(7002800.673, mm**4),
        torsional_constant=Quantity(553076.2107, mm**4),
        major_axis_elastic_section_modulus=Quantity(978491.0105, mm**3),
        minor_axis_elastic_section_modulus=Quantity(285274.0505, mm**3),
        major_axis_plastic_section_modulus=Quantity(1191973.082, mm**3),
        minor_axis_plastic_section_modulus=Quantity(163438.2562, mm**3),
        major_axis_radius_of_gyration=Quantity(159.8102859, mm),
        minor_axis_radius_of_gyration=Quantity(29.09617297, mm),
        polar_radius_of_gyration=Quantity(169.8821487, mm),
        major_axis_shear_centroid=Quantity(0, mm),
        minor_axis_shear_centroid=Quantity(49.73961878, mm),
        warping_constant=Quantity(2.13579e11, mm**6),
    ),
}

area_properties_inputs = [
    (sections[key], value) for key, value in expected_area_properties.items()
]


@mark.parametrize("section, exp_area_prop", area_properties_inputs)
def test_area_properties(
    section: SectionChecks, exp_area_prop: AreaProperties
):
    calculated, expected = same_units_dictionary_simplify_for_test_assert(
        asdict(section.area_properties), asdict(exp_area_prop)
    )
    assert calculated == expected
