from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Union, Callable

import numpy as np
import pandas as pd
import sympy as sp

from sympy.physics.units.quantities import Quantity
from sympy.physics.units.util import convert_to
from sympy.physics.units import m

from structure_scripts.symbols.symbols import (
    Omega,
    phi,
    nominal_stress,
    nominal_body_area,
    nominal_tensile_stress,
    nominal_shear_stress,
    required_shear_stress,
    required_tensile_stress, )
from structure_scripts.units.sympy_units import kN, MPa
from structure_scripts.aisc.criteria import (
    Criteria,
    DesignStrengthFromNominalMixin,
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


# (
#     nominal_body_area,
#     nominal_stress,
#     nominal_tensile_stress,
#     Fnt_l,
#     nominal_shear_stress,
#     required_tensile_stress,
#     required_shear_stress,
#     Omega,
#     phi,
# ) = sp.var("A_b, F_n, F_nt, F_nt^', F_nv, frt, f_rv, Omega, phi")

DESIGN_TYPE_FACTOR_TABLE: dict[DesignType, sp.core.Symbol] = {
    DesignType.ASD: Omega,
    DesignType.LRFD: phi,
}


@dataclass(frozen=True)
class BoltStrength(DesignStrengthFromNominalMixin):
    """
    Fn = Nominal tensile or shear stress\n
    Ab = Nominal body area of bolt (threaded or unthreaded)
    """

    nominal_stress: Quantity
    nominal_body_area: Quantity
    n_bolts: int = 1
    # typ: StrengthType = StrengthType.SHEAR

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2, load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq(self) -> sp.core.Expr:
        return nominal_stress * nominal_body_area

    @cached_property
    def nominal_strength(self):
        return (
                    self._nominal_str_eq.evalf(
                        subs={
                            nominal_stress: self.nominal_stress,
                            nominal_body_area: self.nominal_body_area,
                        },
                    )
                    * self.n_bolts
        )

    @cached_property
    def latex_nominal_expression(self):
        return f"R_n = {sp.latex(self._nominal_str_eq)}"

    def numerical_strength_expression(self, unit: Quantity = kN):
        return f"R_n = {sp.latex(self._nominal_str_eq.evalf(subs={nominal_stress: self.nominal_stress, nominal_body_area: self.nominal_body_area}))} = {sp.latex(convert_to(self.nominal_strength, unit))}"

    @cached_property
    def detailed_results(self) -> dict[str, Union[Quantity, float, None]]:
        return {NOMINAL_STRENGTH: self.nominal_strength}

    def rule_check(
        self, required_strength: Quantity, design_criteria: DesignType
    ):
        return required_strength / self.design_strength(design_criteria)


def _nominal_stress_eq(
    F1t: sp.Symbol, F2t: sp.Symbol, f: sp.Symbol, design_criteria: DesignType
) -> sp.Expr:
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

    nominal_body_area: Quantity
    nominal_tensile_stress: Quantity
    nominal_shear_stress: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2, load_resistance_factor=0.75)

    @cached_property
    def _available_tensile_stress_lrfd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_tensile_stress,
            design_type=DesignType.LRFD,
        )

    @cached_property
    def _available_shear_stress_lrfd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_shear_stress,
            design_type=DesignType.LRFD,
        )

    @cached_property
    def _available_tensile_stress_asd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_tensile_stress,
            design_type=DesignType.ASD,
        )

    @cached_property
    def _available_shear_stress_asd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_shear_stress,
            design_type=DesignType.ASD,
        )

    def _available_tensile_stress(self, design_criteria: DesignType):
        table = {
            DesignType.ASD: self._available_tensile_stress_asd,
            DesignType.LRFD: self._available_tensile_stress_lrfd,
        }
        return table[design_criteria]

    def _available_shear_stress(self, design_criteria: DesignType):
        table = {
            DesignType.ASD: self._available_shear_stress_asd,
            DesignType.LRFD: self._available_shear_stress_lrfd,
        }
        return table[design_criteria]

    @cached_property
    def available_shear_stress_asd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_shear_stress,
            design_type=DesignType.ASD,
        )

    @cached_property
    def _corrected_nominal_tensile_stress_eq_lrfd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=nominal_tensile_stress,
            F2t=nominal_shear_stress,
            f=required_shear_stress,
            design_criteria=DesignType.LRFD,
        )

    @cached_property
    def _corrected_nominal_tensile_stress_eq_asd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=nominal_tensile_stress,
            F2t=nominal_shear_stress,
            f=required_shear_stress,
            design_criteria=DesignType.ASD,
        )

    @cached_property
    def _corrected_nominal_shear_stress_eq_lrfd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=nominal_shear_stress,
            F2t=nominal_tensile_stress,
            f=required_tensile_stress,
            design_criteria=DesignType.LRFD,
        )

    @cached_property
    def _corrected_nominal_shear_stress_eq_asd(self) -> sp.core.Expr:
        return _nominal_stress_eq(
            F1t=nominal_shear_stress,
            F2t=nominal_tensile_stress,
            f=required_tensile_stress,
            design_criteria=DesignType.ASD,
        )

    def _corrected_nominal_tensile_stress_lrfd(
        self, required_shear_stress_: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_tensile_stress_eq_lrfd.evalf(
                    subs={
                        nominal_tensile_stress: self.nominal_tensile_stress,
                        nominal_shear_stress: self.nominal_shear_stress,
                        phi: self.criteria.load_resistance_factor,
                        required_shear_stress: required_shear_stress_,
                    }
                ),
                MPa,
            ),
            convert_to(self.nominal_tensile_stress, MPa),
        )

    def _corrected_nominal_shear_stress_lrfd(
        self, required_tensile_stress_: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_shear_stress_eq_lrfd.evalf(
                    subs={
                        nominal_tensile_stress: self.nominal_tensile_stress,
                        nominal_shear_stress: self.nominal_shear_stress,
                        phi: self.criteria.load_resistance_factor,
                        required_tensile_stress: required_tensile_stress_,
                    }
                ),
                MPa,
            ),
            convert_to(self.nominal_shear_stress, MPa),
        )

    def _corrected_nominal_tensile_stress_asd(
        self, required_shear_stress_: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_tensile_stress_eq_asd.evalf(
                    subs={
                        nominal_tensile_stress: self.nominal_tensile_stress,
                        nominal_shear_stress: self.nominal_shear_stress,
                        Omega: self.criteria.allowable_strength,
                        required_shear_stress: required_shear_stress_,
                    }
                ),
                MPa,
            ),
            convert_to(self.nominal_tensile_stress, MPa),
        )

    def _corrected_nominal_shear_stress_asd(
        self, required_tensile_stress_: Quantity
    ) -> Quantity:
        return min(
            convert_to(
                self._corrected_nominal_shear_stress_eq_asd.evalf(
                    subs={
                        nominal_tensile_stress: self.nominal_tensile_stress,
                        nominal_shear_stress: self.nominal_shear_stress,
                        Omega: self.criteria.allowable_strength,
                        required_tensile_stress: required_tensile_stress_,
                    }
                ),
                MPa,
            ),
            convert_to(self.nominal_tensile_stress, MPa),
        )

    def _tensile_design_stress(
        self, required_shear_stress_: Quantity, design_criteria: DesignType
    ):
        table: dict[DesignType, Callable[[Quantity], Quantity]] = {
            DesignType.ASD: self._corrected_nominal_tensile_stress_asd,
            DesignType.LRFD: self._corrected_nominal_tensile_stress_lrfd,
        }
        return table[design_criteria](required_shear_stress_)

    def _shear_design_stress(
        self, required_tensile_stress_: Quantity, design_criteria: DesignType
    ):
        table: dict[DesignType, Callable[[Quantity], Quantity]] = {
            DesignType.ASD: self._corrected_nominal_shear_stress_asd,
            DesignType.LRFD: self._corrected_nominal_shear_stress_lrfd,
        }
        return table[design_criteria](required_tensile_stress_)

    def rule_check(
        self,
        required_shear_strength_: Quantity,
        required_tensile_strength_: Quantity,
        design_criteria: DesignType = DesignType.ASD,
    ) -> pd.DataFrame:
        required_shear_stress_ = (
            required_shear_strength_ / self.nominal_body_area
        )
        required_tensile_stress_ = (
            required_tensile_strength_ / self.nominal_body_area
        )
        # load_ratios = (
        #     ratio_simplify(required_shear_stress, self._available_shear_stress(design_criteria), unit=MPa),
        #     ratio_simplify(required_tensile_stress, self._available_tensile_stress(design_criteria), unit=MPa)
        #
        # )
        # governing_load = max(load_ratios)

        tensile_ds = self._tensile_design_stress(
            required_shear_stress_=required_shear_stress_,
            design_criteria=design_criteria,
        )
        available_tensile_str = self.criteria.design_strength(
            nominal_strength=tensile_ds * self.nominal_body_area,
            design_type=design_criteria,
        )

        shear_ds = self._shear_design_stress(
            required_tensile_stress_=required_tensile_stress_,
            design_criteria=design_criteria,
        )
        available_shear_str = self.criteria.design_strength(
            nominal_strength=shear_ds * self.nominal_body_area,
            design_type=design_criteria,
        )
        data = (
            (required_tensile_strength_, available_tensile_str),
            (required_shear_strength_, available_shear_str),
        )
        rule_checks = np.array(
            tuple(
                ratio_simplify(required_str, available_str, kN)
                for required_str, available_str in data
            )
        )
        # i = rule_checks.argmax()
        # table = {0: "tensile", 1: "shear"}
        return pd.DataFrame(
            [rule_checks], columns=[BOLT_TENSILE_STRENGTH, BOLT_SHEAR_STRENGTH]
        )


if __name__ == "__main__":
    pass
