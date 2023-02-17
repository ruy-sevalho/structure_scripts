from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from pandas import DataFrame
from sympy.physics.units import Quantity
from sympy import Expr

from structure_scripts.aisc.criteria import (
    DesignStrengthMixin,
    Criteria,
    DesignType,
)
from structure_scripts.symbols.symbols import (
    yield_stress,
    gross_area,
    ultimate_stress,
    effective_net_area,
    gross_shear_area,
    net_shear_area,
    tension_distribution_factor,
    net_tension_area,
)

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
        return yield_stress * gross_area

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={yield_stress: self.Fy, gross_area: self.Ag}
        )


@dataclass(frozen=True)
class TensileRupture(DesignStrengthMixin):
    """
    Fu = ultimate stress\n
    Ae = net area\n
    """

    ultimate_stress: Quantity
    net_area: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2.0, load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return ultimate_stress * effective_net_area

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={
                ultimate_stress: self.ultimate_stress,
                effective_net_area: self.net_area,
            }
        )


@dataclass(frozen=True)
class ShearYielding(DesignStrengthMixin):
    """
    Fy = yield stress
    Agv = gross area subject to shear
    """

    yield_stress: Quantity
    gross_shear_area: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=1.5, load_resistance_factor=1)

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return 0.60 * yield_stress * gross_shear_area

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={
                yield_stress: self.yield_stress,
                gross_shear_area: self.gross_shear_area,
            }
        )


@dataclass(frozen=True)
class ShearRupture(DesignStrengthMixin):
    """
    Fu = Ultimate stress
    Anv = net area subject to shear
    """

    ultimate_stress: Quantity
    net_shear_area: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2.0, load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return 0.60 * ultimate_stress * net_shear_area

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={
                ultimate_stress: self.ultimate_stress,
                net_shear_area: self.net_shear_area,
            }
        )


@dataclass(frozen=True)
class TensileYieldAndRupture:
    """
    Fy = yield stress\n
    Ag = gross area\n
    Fu = ultimate stress\n
    Ae = net area\n
    """

    yield_stress: Quantity
    gross_area: Quantity
    ultimate_stress: Quantity
    net_area: Quantity

    @cached_property
    def tensile(self):
        return TensileYield(self.yield_stress, self.gross_area)

    @cached_property
    def rupture(self):
        return TensileRupture(self.ultimate_stress, self.net_area)

    def results(self, design_criteria: DesignType = DesignType.ASD):
        return DataFrame(
            [[self.tensile.design_strength(design_criteria)]],
            columns=[TENSILE_RUPTURE],
        )


class TensionDistribution(Enum):
    UNIFORM = 1.0
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

    yield_stress: Quantity
    ultimate_stress: Quantity
    net_shear_area: Quantity
    net_tension_area: Quantity
    gross_shear_area: Quantity
    gross_tension_area: Quantity
    tension_distribution_factor: TensionDistribution = (
        TensionDistribution.NON_UNIFORM
    )

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2.0, load_resistance_factor=0.75)

    @cached_property
    def _nominal_str_eq1(self) -> Expr:
        return (
            0.60 * ultimate_stress * net_shear_area
            + tension_distribution_factor * ultimate_stress * net_tension_area
        )

    @cached_property
    def _nominal_str_eq2(self) -> Expr:
        return (
            0.60 * yield_stress * gross_shear_area
            + tension_distribution_factor * ultimate_stress * net_tension_area
        )

    @cached_property
    def _nominal_str1(self) -> Quantity:
        return self._nominal_str_eq1.evalf(
            subs={
                ultimate_stress: self.ultimate_stress,
                net_shear_area: self.net_shear_area,
                net_tension_area: self.net_tension_area,
                tension_distribution_factor: self.tension_distribution_factor.value,
            }
        )

    @cached_property
    def _nominal_str2(self) -> Quantity:
        return self._nominal_str_eq2.evalf(
            subs={
                ultimate_stress: self.ultimate_stress,
                yield_stress: self.yield_stress,
                gross_shear_area: self.gross_shear_area,
                net_tension_area: self.net_tension_area,
                tension_distribution_factor: self.tension_distribution_factor.value,
            }
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return min(self._nominal_str1, self._nominal_str2)
