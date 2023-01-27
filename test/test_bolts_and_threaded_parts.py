from pytest import mark, approx
from quantities import Quantity, mm, MPa, N

from structure_scripts.aisc.connections.bolts import (
    BoltSpacing,
    check_bolt_minimum_spacing,
)
from structure_scripts.aisc.connections.bolts import BoltStrength
from structure_scripts.helpers import same_units_simplify


@mark.parametrize(
    "nominal_diameter, spacing, expected_criteria",
    [
        (10 * mm, 10 * mm, BoltSpacing.REJECTED),
        (10 * mm, 29 * mm, BoltSpacing.ACCEPTED),
        (10 * mm, 35 * mm, BoltSpacing.PREFERRED),
    ],
)
def test_minimum_spacing(
    nominal_diameter: Quantity,
    spacing: Quantity,
    expected_criteria: BoltSpacing,
):
    assert (
        check_bolt_minimum_spacing(nominal_diameter, spacing)
        == expected_criteria
    )


@mark.parametrize(
    "nominal_body_area, nominal_stress, expected_nominal_strength",
    [
        (10 * mm**2, 250 * MPa, 2500 * N),
    ],
)
def test_bolt_strength(
    nominal_body_area: Quantity,
    nominal_stress: Quantity,
    expected_nominal_strength: Quantity,
):
    criteria = BoltStrength(
        nominal_body_area=nominal_body_area, nominal_stress=nominal_stress
    )
    calc, exp = same_units_simplify(
        criteria.nominal_strength, expected_nominal_strength
    )
    assert calc == approx(exp)
