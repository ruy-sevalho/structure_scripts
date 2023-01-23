from pytest import mark
from quantities import Quantity, mm

from structure_scripts.aisc.connections.bolts import BoltSpacing, check_bolt_minimun_spacing


@mark.parametrize(
    "nominal_diameter, spacing, expected_criteria",
    [
        (10*mm, 10*mm, BoltSpacing.REJECTED),
        (10*mm, 29*mm, BoltSpacing.ACCEPTED),
        (10*mm, 35*mm, BoltSpacing.PREFERRED),
    ]
)
def test_minimum_spacing(nominal_diameter: Quantity, spacing: Quantity, expected_criteria: BoltSpacing):
    assert check_bolt_minimun_spacing(nominal_diameter, spacing) == expected_criteria
