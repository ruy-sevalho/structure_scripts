from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Union

import sympy as sp
from quantities import Quantity

from structure_scripts.aisc.criteria import (
    Criteria,
    DesignStrengthMixin,
    NOMINAL_STRENGTH,
)
from structure_scripts.helpers import ratio_simplify

BOLT_SPACING_RATIO_ACCEPTED = 8 / 3
BOLT_SPACING_RATIO_PREFERRED = 3


class BoltSpacing(str, Enum):
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    PREFERRED = "preferred"


def check_bolt_minimum_spacing(
    nominal_diameter: Quantity, bolt_spacing: Quantity
) -> BoltSpacing:
    ratio = ratio_simplify(bolt_spacing, nominal_diameter)
    if ratio > BOLT_SPACING_RATIO_PREFERRED:
        return BoltSpacing.PREFERRED
    if ratio > BOLT_SPACING_RATIO_ACCEPTED:
        return BoltSpacing.ACCEPTED
    return BoltSpacing.REJECTED


class BoltStrength(str, Enum):
    SHEAR = "shear"
    TENSION = "tension"


@dataclass(frozen=True)
class BoltStrength(DesignStrengthMixin):
    nominal_stress: Quantity
    nominal_body_area: Quantity
    criteria: Criteria(allowable_strength=2.0, load_resistance_factor=0.75)

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self.nominal_stress * self.nominal_body_area

    @cached_property
    def detailed_results(self) -> dict[str, Union[Quantity, float, None]]:
        return {NOMINAL_STRENGTH: self.nominal_strength}
