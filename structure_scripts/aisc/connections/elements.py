from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from pandas import DataFrame
from sympy.physics.units import Quantity
from sympy import Expr

from structure_scripts.aisc.criteria import DesignStrengthMixin, Criteria, DesignType
from structure_scripts.symbols.symbols import Fy, Ag, Fu, Ae, Agv, Anv, Ubs, Ant

TENSILE_YIELDING = "tensile yield"
TENSILE_RUPTURE = "tensile rupture"


@dataclass(frozen=True)
class TensileYield(DesignStrengthMixin):
    """
    Fy = yield stress\n
    Ag = gross area\n
    """

    Fy: Quantity
    Ag: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria()

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return Fy * Ag

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={Fy: self.Fy, Ag: self.Ag}
        )


@dataclass(frozen=True)
class TensileRupture(DesignStrengthMixin):
    """
    Fu = ultimate stress\n
    Ae = net area\n
    """

    Fu: Quantity
    Ae: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2., load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return Fu * Ae

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={Fu: self.Fu, Ae: self.Ae}
        )


@dataclass(frozen=True)
class ShearYielding(DesignStrengthMixin):
    """
    Fy = yield stress
    Agv = gross area subject to shear
    """

    Fy: Quantity
    Agv: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=1.5, load_resistance_factor=1)

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return 0.60 * Fy * Agv

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={Fy: self.Fy, Agv: self.Agv}
        )


@dataclass(frozen=True)
class ShearRupture(DesignStrengthMixin):
    """
    Fu = Ultimate stress
    Anv = net area subject to shear
    """

    Fu: Quantity
    Anv: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2., load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return 0.60 * Fu * Anv

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={Fu: self.Fu, Anv: self.Anv}
        )


@dataclass(frozen=True)
class TensileYieldAndRupture:
    """
    Fy = yield stress\n
    Ag = gross area\n
    Fu = ultimate stress\n
    Ae = net area\n
    """

    Fy: Quantity
    Ag: Quantity
    Fu: Quantity
    Ae: Quantity

    @cached_property
    def tensile(self):
        return TensileYield(self.Fy, self.Ag)

    @cached_property
    def rupture(self):
        return TensileRupture(self.Fu, self.Ae)

    def results(self, design_criteria: DesignType = DesignType.ASD):
        return DataFrame(
            [
                [
                    self.tensile.design_strength(design_criteria)
                ]
            ],
            columns=[TENSILE_RUPTURE]
        )


class TensionDistribution(Enum):
    UNIFORM = 1.
    NON_UNIFORM = 0.5


@dataclass(frozen=True)
class BlockShearStrength(DesignStrengthMixin):
    """
    Fy = yield stress\n
    Fu = ultimate stress\n
    Anv = net area subjected to shear\n
    Ant = net area subjected to tension\n
    Agv = gross area subjected to shear\n
    Agt = gross area subjected to shear\n
    Ubs = tension uniformity\n
    """
    Fy: Quantity
    Fu: Quantity
    Anv: Quantity
    Ant: Quantity
    Agv: Quantity
    Agt: Quantity
    Ubs: TensionDistribution = TensionDistribution.NON_UNIFORM

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2., load_resistance_factor=.75)

    @cached_property
    def _nominal_str_eq1(self) -> Expr:
        return 0.60 * Fu * Anv + Ubs * Fu * Ant

    @cached_property
    def _nominal_str_eq2(self) -> Expr:
        return 0.60 * Fy * Agv + Ubs * Fu * Ant

    @cached_property
    def _nominal_str1(self) -> Quantity:
        return self._nominal_str_eq1.evalf(
            subs={Fu: self.Fu, Anv: self.Anv, Ant: self.Ant, Ubs: self.Ubs.value}
        )

    @cached_property
    def _nominal_str2(self) -> Quantity:
        return self._nominal_str_eq2.evalf(
            subs={Fu: self.Fu, Fy: self.Fy, Agv: self.Agv, Ant: self.Ant, Ubs: self.Ubs.value}
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return min(self._nominal_str1, self._nominal_str2)