from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from typing import Union, Callable

import numpy as np
import pandas as pd
import sympy as sp

from sympy.physics.units.quantities import Quantity
from sympy.physics.units.util import convert_to
from sympy.physics.units import m, mm
from structure_scripts.units.sympy_units import kN, MPa
from structure_scripts.aisc.criteria import (
    Criteria,
    DesignStrengthMixin,
    NOMINAL_STRENGTH,
    DesignType,
)
from structure_scripts.units.sympy_units import ratio_simplify

BOLT_SPACING_RATIO_ACCEPTED = 8 / 3
BOLT_SPACING_RATIO_PREFERRED = 3

BOLT_TENSILE_STRENGTH = "bolt tens str"
BOLT_SHEAR_STRENGTH = "bolt shear str"


class BoltSpacing(str, Enum):
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    PREFERRED = "preferred"


def check_bolt_minimum_spacing(
    nominal_diameter: Quantity, bolt_spacing: Quantity
) -> BoltSpacing:
    ratio = ratio_simplify(bolt_spacing, nominal_diameter, m)
    if ratio > BOLT_SPACING_RATIO_PREFERRED:
        return BoltSpacing.PREFERRED
    if ratio > BOLT_SPACING_RATIO_ACCEPTED:
        return BoltSpacing.ACCEPTED
    return BoltSpacing.REJECTED


class StrengthType(str, Enum):
    SHEAR = "shear"
    TENSION = "tension"


Ab, Fn, Fnt, Fnt_l, Fnv, frt, frv, Omega, phi = sp.var(
    "A_b, F_n, F_nt, F_nt^', F_nv, frt, f_rv, Omega, phi"
)

DESIGN_TYPE_FACTOR_TABLE: dict[DesignType, sp.core.Symbol] = {
    DesignType.ASD: Omega, DesignType.LRFD: phi
}


@dataclass(frozen=True)
class BoltStrength(DesignStrengthMixin):
    """Fn = Nominal tensile or shear stress\n
    Ab = Nominal body area of bolt (threaded or unthreaded)
    """

    Fn: Quantity
    Ab: Quantity
    typ: StrengthType = StrengthType.SHEAR

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2, load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq(self) -> sp.core.Expr:
        return Fn * Ab

    @cached_property
    def nominal_strength(self):
        return self._nominal_str_eq.evalf(
            subs={Fn: self.Fn, Ab: self.Ab},
        )

    @cached_property
    def latex_nominal_expression(self):
        return f"R_n = {sp.latex(self._nominal_str_eq)}"

    def numerical_strength_expression(self, unit: Quantity = kN):
        return f"R_n = {sp.latex(self._nominal_str_eq.evalf(subs={Fn: self.Fn, Ab: self.Ab}))} = {sp.latex(convert_to(self.nominal_strength, unit))}"

    @cached_property
    def detailed_results(self) -> dict[str, Union[Quantity, float, None]]:
        return {NOMINAL_STRENGTH: self.nominal_strength}

    def rule_check(
        self, required_strength: Quantity, design_criteria: DesignType
    ):
        return required_strength / self.design_strength(design_criteria)


def _nominal_stress_eq(F1t: sp.Symbol, F2t: sp.Symbol, f:sp.Symbol, design_criteria: DesignType) -> sp.Expr:
    design_factor = DESIGN_TYPE_FACTOR_TABLE[design_criteria]
    if design_criteria == DesignType.ASD:
        return 1.3 * F1t - design_factor * F1t / F2t * f
    return 1.3 * F1t - F1t / (design_factor * F2t) * f


@dataclass(frozen=True)
class BoltCombinedTensionAndShear:
    """
    Fnt = nominal tensile stress\n
    Fnv = nominal shear stress\n
    Ab = Nominal body area of bolt (threaded or unthreaded)\n
    frv = required shear stress
    """

    Ab: Quantity
    Fnt: Quantity
    Fnv: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2, load_resistance_factor=0.75)

    @cached_property
    def _available_tensile_stress_lrfd(self):
        return self.criteria.design_strength(nominal_strength=self.Fnt, design_type=DesignType.LRFD)

    @cached_property
    def _available_shear_stress_lrfd(self):
        return self.criteria.design_strength(nominal_strength=self.Fnv, design_type=DesignType.LRFD)

    @cached_property
    def _available_tensile_stress_asd(self):
        return self.criteria.design_strength(nominal_strength=self.Fnt, design_type=DesignType.ASD)

    @cached_property
    def _available_shear_stress_asd(self):
        return self.criteria.design_strength(nominal_strength=self.Fnv, design_type=DesignType.ASD)

    def _available_tensile_stress(self, design_criteria: DesignType):
        table = {
            DesignType.ASD: self._available_tensile_stress_asd,
            DesignType.LRFD: self._available_tensile_stress_lrfd
        }
        return table[design_criteria]

    def _available_shear_stress(self, design_criteria: DesignType):
        table = {
            DesignType.ASD: self._available_shear_stress_asd,
            DesignType.LRFD: self._available_shear_stress_lrfd
        }
        return table[design_criteria]

    @cached_property
    def available_shear_stress_asd(self):
        return self.criteria.design_strength(nominal_strength=self.Fnv, design_type=DesignType.ASD)

    @cached_property
    def _corrected_nominal_tensile_stress_eq_lrfd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=Fnt, F2t=Fnv, f=frv, design_criteria=DesignType.LRFD
        )

    @cached_property
    def _corrected_nominal_tensile_stress_eq_asd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=Fnt, F2t=Fnv, f=frv, design_criteria=DesignType.ASD
        )

    @cached_property
    def _corrected_nominal_shear_stress_eq_lrfd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=Fnv, F2t=Fnt, f=frt, design_criteria=DesignType.LRFD
        )

    @cached_property
    def _corrected_nominal_shear_stress_eq_asd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=Fnv, F2t=Fnt, f=frt, design_criteria=DesignType.ASD
        )

    def _corrected_nominal_tensile_stress_lrfd(
        self, required_shear_stress: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_tensile_stress_eq_lrfd.evalf(
                    subs={
                        Fnt: self.Fnt,
                        Fnv: self.Fnv,
                        phi: self.criteria.load_resistance_factor,
                        frv: required_shear_stress,
                    }
                ),
                MPa
            ),
            convert_to(
                self.Fnt,
                MPa
            )
        )

    def _corrected_nominal_shear_stress_lrfd(
        self, required_tensile_stress: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_shear_stress_eq_lrfd.evalf(
                    subs={
                        Fnt: self.Fnt,
                        Fnv: self.Fnv,
                        phi: self.criteria.load_resistance_factor,
                        frt: required_tensile_stress,
                    }
                ),
                MPa
            ),
            convert_to(
                self.Fnv,
                MPa
            )
        )

    def _corrected_nominal_tensile_stress_asd(
        self, required_shear_stress: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_tensile_stress_eq_asd.evalf(
                    subs={
                        Fnt: self.Fnt,
                        Fnv: self.Fnv,
                        Omega: self.criteria.allowable_strength,
                        frv: required_shear_stress,
                    }
                ),
                MPa,
            ),
            convert_to(self.Fnt, MPa),
        )

    def _corrected_nominal_shear_stress_asd(
        self, required_tensile_stress: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_shear_stress_eq_asd.evalf(
                    subs={
                        Fnt: self.Fnt,
                        Fnv: self.Fnv,
                        Omega: self.criteria.allowable_strength,
                        frt: required_tensile_stress,
                    }
                ),
                MPa,
            ),
            convert_to(self.Fnt, MPa),
        )

    def _tensile_design_stress(
        self, required_shear_stress: Quantity, design_criteria: DesignType
    ):
        table: dict[DesignType, Callable[[Quantity], Quantity]] = {
            DesignType.ASD: self._corrected_nominal_tensile_stress_asd,
            DesignType.LRFD: self._corrected_nominal_tensile_stress_lrfd,
        }
        return table[design_criteria](required_shear_stress)

    def _shear_design_stress(
        self, required_tensile_stress: Quantity, design_criteria: DesignType
    ):
        table: dict[DesignType, Callable[[Quantity], Quantity]] = {
            DesignType.ASD: self._corrected_nominal_shear_stress_asd,
            DesignType.LRFD: self._corrected_nominal_shear_stress_lrfd,
        }
        return table[design_criteria](required_tensile_stress)

    def rule_check(
        self,
        required_shear_strength: Quantity,
        required_tensile_strength: Quantity,
        design_criteria: DesignType = DesignType.ASD,
    ) -> pd.DataFrame:
        required_shear_stress = required_shear_strength / self.Ab
        required_tensile_stress = required_tensile_strength / self.Ab
        # load_ratios = (
        #     ratio_simplify(required_shear_stress, self._available_shear_stress(design_criteria), unit=MPa),
        #     ratio_simplify(required_tensile_stress, self._available_tensile_stress(design_criteria), unit=MPa)
        #
        # )
        # governing_load = max(load_ratios)

        tensile_ds = self._tensile_design_stress(
            required_shear_stress=required_shear_stress,
            design_criteria=design_criteria,
        )
        available_tensile_str = self.criteria.design_strength(
            nominal_strength=tensile_ds * self.Ab, design_type=design_criteria
        )

        shear_ds = self._shear_design_stress(
            required_tensile_stress=required_tensile_stress,
            design_criteria=design_criteria,
        )
        available_shear_str = self.criteria.design_strength(
            nominal_strength=shear_ds * self.Ab, design_type=design_criteria
        )
        data = ((required_tensile_strength, available_tensile_str), (required_shear_strength, available_shear_str))
        rule_checks = np.array(tuple(ratio_simplify(required_str, available_str, kN) for required_str, available_str in data))
        # i = rule_checks.argmax()
        # table = {0: "tensile", 1: "shear"}
        return pd.DataFrame([rule_checks], columns=[BOLT_TENSILE_STRENGTH, BOLT_SHEAR_STRENGTH])


lc, t, Fu, d = sp.var("l_c, t, F_u, d")


class BearingStrengthType(Enum):
    """See J.3.10 Bearing Strength at Bolt Holes"""
    DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED = (1.2, 2.4)
    DEFORMATION_AT_SERVICE_LOAD_ALLOWED = (1.5, 2.3)
    LONG_SLOTTED_LOAD_PERPENDICULAR_TO_SLOT = (1.0, 2.0)


@dataclass(frozen=True)
class BoltHolesBearingStrength(DesignStrengthMixin):
    """
    Fu = specified minimum tensile strength of the connected material\n
    d = nominal bolt diameter\n
    lc = clear distance, in the direction of the force, between the edge of the hole and
    the edge of the adjacent hole or edge of the material\n
    t = thickness of connected material
    """
    Fu: Quantity
    d: Quantity
    lc: Quantity
    t: Quantity
    connection_type: BearingStrengthType = BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2, load_resistance_factor=0.75)

    @cached_property
    def _nominal_load1_eq(self) -> sp.Expr:
        return self.connection_type.value[0] * lc * t * Fu

    @cached_property
    def _nominal_load2_eq(self) -> sp.Expr:
        return self.connection_type.value[1] * d * t * Fu

    @cached_property
    def _nominal_load1(self) -> Quantity:
        return self._nominal_load1_eq.evalf(
            subs={lc: self.lc, t: self.t, Fu: self.Fu}
        )

    @cached_property
    def _nominal_load2(self) -> Quantity:
        return self._nominal_load2_eq.evalf(
            subs={d: self.d, t: self.t, Fu: self.Fu}
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return min(self._nominal_load1, self._nominal_load2)


if __name__ == "__main__" :
    b = BoltHolesBearingStrength(
        Fu=350 * MPa,
        d=25*mm,
        lc=50*mm,
        t=8*mm
    )
    sp.print_latex(b._nominal_load1_eq)