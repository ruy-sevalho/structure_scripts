import numpy as np
from pytest import mark, approx
from quantities import Quantity, m

# from structure_scripts.section_calc import (
#     _rotation_and_translation_of_2d_point_coordinate_system,
# )
#
#
# @mark.parametrize(
#     "point, new_coord_sys_origen, new_coord_sys_angle, degrees, expected",
#     [
#         (
#             Quantity(np.array([1.0, 1]), m),
#             Quantity(np.array([0.5, 0.5]), m),
#             45,
#             True,
#             Quantity(np.array([0.0, 0.70710678]), m),
#         ),
#     ],
# )
# def test_point_rotation_and_translation(
#     point: Quantity,
#     new_coord_sys_origen: Quantity,
#     new_coord_sys_angle: float,
#     degrees: bool,
#     expected: Quantity,
# ):
#     rotated_point = _rotation_and_translation_of_2d_point_coordinate_system(
#         point=point,
#         new_coord_sys_origen=new_coord_sys_origen,
#         new_coord_sys_angle=new_coord_sys_angle,
#         degrees=degrees,
#     )
#     rotated_point = rotated_point.simplified.magnitude
#     expected = expected.simplified.magnitude
#     assert rotated_point == approx(expected)
