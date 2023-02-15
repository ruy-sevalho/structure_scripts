from sympy.physics.units import Quantity, force, pressure, convert_to
from sympy.physics.units.systems import SI

kN = Quantity("kilonewton", abbrev="kN", is_prefixed=True)
MPa = Quantity("megapascal", abbrev="MPa", is_prefixed=True)
# SI.set_quantity_dimension(kN, force)
# SI.set_quantity_dimension(MPa, pressure)


def same_units_simplify(
    q1: Quantity, q2: Quantity, unit: Quantity, strip_units: bool = False
):
    q1_convert, q2_convert = (convert_to(q1, unit), convert_to(q2, unit))
    if strip_units:
        q1_convert, q2_convert = (q1_convert.args[0], q2_convert.args[0])
    return q1_convert, q2_convert


def ratio_simplify(q1: Quantity, q2: Quantity, unit: Quantity) -> float:
    q1 = convert_to(q1, unit)
    q2 = convert_to(q2, unit)
    r: Quantity = q1 / q2
    if len(r.args):
        raise ValueError("q1/q2 is not dimensionless")
    return r
