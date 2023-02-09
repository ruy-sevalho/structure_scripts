from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Union

import sympy as sp

from sympy.physics.units.quantities import Quantity
from sympy.physics.units.util import convert_to

from structure_scripts.units.units import kN
from structure_scripts.aisc.criteria import (
    Criteria,
    DesignStrengthMixin,
    NOMINAL_STRENGTH,
)
from structure_scripts.units.units import ratio_simplify

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


class StrengthType(str, Enum):
    SHEAR = "shear"
    TENSION = "tension"


Fn, Ab = sp.var("F_n, A_b")


@dataclass(frozen=True)
class BoltStrength:
    Fn: Quantity
    Ab: Quantity
    typ: StrengthType = StrengthType.SHEAR

    @cached_property
    def nominal_strength_expression(self) -> sp.core.Expr:
        return Fn * Ab

    @cached_property
    def nominal_strength(self):
        return self.nominal_strength_expression.evalf(
            subs={Fn: self.Fn, Ab: self.Ab},
        )

    @cached_property
    def latex_nominal_expression(self):
        return f"R_n = {sp.latex(self.nominal_strength_expression)}"

    def numerical_strength_expression(self, unit: Quantity = kN):
        return f"R_n = {sp.latex(self.nominal_strength_expression.evalf(subs={Fn: self.Fn, Ab: self.Ab}))} = {sp.latex(convert_to(self.nominal_strength, unit))}"

    @cached_property
    def detailed_results(self) -> dict[str, Union[Quantity, float, None]]:
        return {NOMINAL_STRENGTH: self.nominal_strength}
