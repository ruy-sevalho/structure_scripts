from typing import Collection

from sympy.physics.units import Quantity, force, pressure, convert_to
from sympy.physics.units.systems import SI

kN = Quantity("kilonewton", abbrev="kN", is_prefixed=True)
MPa = Quantity("megapascal", abbrev="MPa", is_prefixed=True)
# SI.set_quantity_dimension(kN, force)
# SI.set_quantity_dimension(MPa, pressure)


def same_units_simplify(
    quantities: Collection[Quantity], unit: Quantity, strip_units: bool = False
):
    q_convert = tuple((convert_to(q, unit) for q in quantities))
    if strip_units:
        q_convert = tuple((q.args[0] for q in q_convert))
    return q_convert


def ratio_simplify(q1: Quantity, q2: Quantity, unit: Quantity) -> float:
    q1 = convert_to(q1, unit)
    q2 = convert_to(q2, unit)
    r: Quantity = q1 / q2
    if len(r.args):
        raise ValueError("q1/q2 is not dimensionless")
    return r
