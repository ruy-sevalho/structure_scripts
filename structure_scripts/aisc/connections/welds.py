from dataclasses import dataclass
from functools import cached_property

from sympy import Expr, sqrt, sin
from sympy.physics.units import Quantity, rad, degrees, convert_to, radian

from structure_scripts.aisc.criteria import DesignStrengthFromNominalMixin, Criteria
from structure_scripts.symbols.symbols import (
    weld_nominal_stress,
    effective_weld_area,
    filler_metal_strength,
    theta,
    weld_size,
    weld_length,
)
from structure_scripts.units.sympy_units import kN


@dataclass(frozen=True)
class FilletWeld(DesignStrengthFromNominalMixin):
    """
    FEXX = filler metal classification strength\n
    D = weld size\n
    l = weld length\n
    theta = angle between load direction and weld axis 0 parallel 90 perpendicular\n
    """

    filler_metal_strength: Quantity
    weld_size: Quantity
    weld_length: Quantity
    theta: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2.0, load_resistance_factor=0.75)

    _nominal_str_eq: Expr = weld_nominal_stress * effective_weld_area
    _Awe_eq: Expr = weld_size * weld_length * sqrt(2) / 2
    _Fnw_eq: Expr = (
        0.60 * filler_metal_strength * (1.0 + 0.50 * sin(theta) ** 1.5)
    )

    @cached_property
    def _effective_weld_area(self) -> Quantity:
        return self._Awe_eq.evalf(
            subs={weld_size: self.weld_size, weld_length: self.weld_length}
        )

    @cached_property
    def _weld_nominal_stress(self) -> Quantity:
        return self._Fnw_eq.evalf(
            subs={
                filler_metal_strength: self.filler_metal_strength,
                theta: convert_to(self.theta, 1.0),
            }
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return convert_to(
            self._nominal_str_eq.evalf(
                subs={
                    weld_nominal_stress: self._weld_nominal_stress,
                    effective_weld_area: self._effective_weld_area,
                }
            ),
            kN,
        )
