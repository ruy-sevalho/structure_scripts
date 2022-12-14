# from dataclasses import asdict
#
# from pytest import mark
# from quantities import Quantity, mm
#
# from test.data import sections
# from structure_scripts.sections_from_dimensions import (
#     AreaProperties,
#     SectionChecks,
# )
# from test.helpers import same_units_dictionary_simplify_for_test_assert
#
# expected_area_properties = {
#     "w_200x10_200x10": AreaProperties(
#         A=Quantity(6000, mm**2),
#         Ix=Quantity(50800000, mm**4),
#         Iy=Quantity(13350000, mm**4),
#         J=Quantity(203333.3333, mm**4),
#         Sx=Quantity(461818.1818, mm**3),
#         Sy=Quantity(133500, mm**3),
#         Zx=Quantity(520000, mm**3),
#         Zy=Quantity(205000, mm**3),
#         rx=Quantity(92.01449161, mm),
#         ry=Quantity(47.16990566, mm),
#         ro=Quantity(103.4005158, mm),
#         xs=Quantity(0, mm),
#         ys=Quantity(0, mm),
#         Cw=Quantity(1.47184e11, mm**6),
#     ),
#     "channel_432x102": AreaProperties(
#         A=Quantity(8271.8, mm**2),
#         Ix=Quantity(211256209.2, mm**4),
#         Iy=Quantity(7002800.673, mm**4),
#         J=Quantity(553076.2107, mm**4),
#         Sx=Quantity(978491.0105, mm**3),
#         Sy=Quantity(285274.0505, mm**3),
#         Zx=Quantity(1191973.082, mm**3),
#         Zy=Quantity(163438.2562, mm**3),
#         rx=Quantity(159.8102859, mm),
#         ry=Quantity(29.09617297, mm),
#         ro=Quantity(169.8821487, mm),
#         xs=Quantity(0, mm),
#         ys=Quantity(49.73961878, mm),
#         Cw=Quantity(2.13579e11, mm**6),
#     ),
# }
#
# area_properties_inputs = [
#     (sections[key], value) for key, value in expected_area_properties.items()
# ]
#
#
# @mark.parametrize("section, exp_area_prop", area_properties_inputs)
# def test_area_properties(
#     section: SectionChecks, exp_area_prop: AreaProperties
# ):
#     calculated, expected = same_units_dictionary_simplify_for_test_assert(
#         asdict(section.area_properties), asdict(exp_area_prop)
#     )
#     assert calculated == expected
