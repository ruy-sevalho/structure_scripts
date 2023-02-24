from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Collection

import sympy as sp
from pandas import DataFrame
from sympy.physics.units import Quantity, convert_to
from sympy import Expr

from examples.sp import kN
from structure_scripts.aisc.criteria import (
    DesignStrengthFromNominalMixin,
    Criteria,
    DesignType, DesignStrengthMixin,
)
from structure_scripts.symbols.symbols import (
    yield_stress,
    gross_area,
    ultimate_stress,
    effective_net_area,
    gross_shear_area,
    net_shear_area,
    tension_distribution_factor,
    net_tension_area, clear_distance, thickness, bolt_diameter,
)

TENSILE_YIELDING = "tensile yield"
TENSILE_RUPTURE = "tensile rupture"


@dataclass(frozen=True)
class TensileYield(DesignStrengthFromNominalMixin):
    """
    J4.1 Strength of Elements in Tension (a)
    """

    yield_stress: Quantity
    gross_area: Quantity

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria()

    @cached_property
    def _nominal_str_eq(self) -> Expr:
        return yield_stress * gross_area

    @cached_property
    def nominal_strength(self) -> Quantity:
        return self._nominal_str_eq.evalf(
            subs={yield_stress: self.yield_stress, gross_area: self.gross_area}
        )


@dataclass(frozen=True)
class TensileRupture(DesignStrengthFromNominalMixin):
    """
    J4.1 Strength of Elements in Tension (b)
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
class ShearYield(DesignStrengthFromNominalMixin):
    """
    J4.2 Strength of Elements in Shear (a)
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
class ShearRupture(DesignStrengthFromNominalMixin):
    """
    J4.2 Strength of Elements in Shear (b)
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
class BlockShearStrength(DesignStrengthFromNominalMixin):
    """
    J4.3 Block Shear Strength
    """

    yield_stress: Quantity
    ultimate_stress: Quantity
    net_shear_area: Quantity
    net_tension_area: Quantity
    gross_shear_area: Quantity
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


class BearingStrengthType(Enum):
    """See J.3.10 Bearing Strength at Bolt Holes"""

    DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED = (1.2, 2.4)
    DEFORMATION_AT_SERVICE_LOAD_ALLOWED = (1.5, 2.3)
    LONG_SLOTTED_LOAD_PERPENDICULAR_TO_SLOT = (1.0, 2.0)


@dataclass(frozen=True)
class BoltHolesBearingStrength(DesignStrengthFromNominalMixin):
    """
    J4.10 Bearing Strength at Bolt Holes
    """

    ultimate_stress: Quantity
    bolt_diameter: Quantity
    clear_distance: Quantity
    thickness: Quantity
    n_bolts: int = 1
    connection_type: BearingStrengthType = (
        BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED
    )

    @cached_property
    def criteria(self) -> Criteria:
        return Criteria(allowable_strength=2, load_resistance_factor=0.75)

    @cached_property
    def _nominal_load1_eq(self) -> sp.Expr:
        return (
            self.connection_type.value[0]
            * clear_distance
            * thickness
            * ultimate_stress
        )

    @cached_property
    def _nominal_load2_eq(self) -> sp.Expr:
        return (
            self.connection_type.value[1]
            * bolt_diameter
            * thickness
            * ultimate_stress
        )

    @cached_property
    def _nominal_load1(self) -> Quantity:
        return self._nominal_load1_eq.evalf(
            subs={
                clear_distance: self.clear_distance,
                thickness: self.thickness,
                ultimate_stress: self.ultimate_stress,
            }
        )

    @cached_property
    def _nominal_load2(self) -> Quantity:
        return self._nominal_load2_eq.evalf(
            subs={
                bolt_diameter: self.bolt_diameter,
                thickness: self.thickness,
                ultimate_stress: self.ultimate_stress,
            }
        )

    @cached_property
    def nominal_strength(self) -> Quantity:
        return min(convert_to(self._nominal_load1, kN), convert_to(self._nominal_load2, kN)) * self.n_bolts


@dataclass
class BoltHolesBearingStrengthMultiple(DesignStrengthMixin):
    ultimate_stress: Quantity
    bolt_diameter: Quantity
    clear_distance_n_bolts_tuples: Collection[tuple[Quantity, int]]
    thickness: Quantity
    connection_type: BearingStrengthType = (
        BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED
    )

    @cached_property
    def _strength_per_clear_distance(self):
        return tuple(
            (
                BoltHolesBearingStrength(
                    ultimate_stress=self.ultimate_stress,
                    bolt_diameter=self.bolt_diameter,
                    clear_distance=value[0],
                    thickness=self.thickness,
                    n_bolts=value[1],
                    connection_type=self.connection_type
                )
                for value in self.clear_distance_n_bolts_tuples
            )
        )

    @cached_property
    def design_strength_asd(self) -> Quantity:
        return sum((strength.design_strength(DesignType.ASD) for strength in self._strength_per_clear_distance))

    @cached_property
    def design_strength_lrfd(self) -> Quantity:
        return sum((strength.design_strength(DesignType.LRFD) for strength in self._strength_per_clear_distance))


