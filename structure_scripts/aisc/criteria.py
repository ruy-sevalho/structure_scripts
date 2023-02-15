from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Protocol, Callable, Optional, Union

from quantities import Quantity

NOMINAL_STRENGTH = "nominal_strength"


class DesignType(str, Enum):
    ASD = "ASD"
    LRFD = "LRFD"


class StrengthType(str, Enum):
    SHEAR = "shear"
    FLEXURAL_BUCKLING_MAJOR_AXIS = "flexural_buckling_major_axis"
    FLEXURAL_BUCKLING_MINOR_AXIS = "flexural_buckling_minor_axis"
    TORSIONAL_BUCKLING = "torsional_buckling"
    YIELD = "yield"
    LATERAL_TORSIONAL_BUCKLING = "lateral_torsional_buckling"
    COMPRESSION_FLANGE_LOCAL_BUCKLING = "compression_flange_local_buckling"
    COMPRESSION_FLANGE_YIELDING = "compression_flange_yielding"
    TENSION_FLANGE_YIELDING = "tension_flange_yielding"


def asd(nominal_strength: Quantity, safety_factor: float) -> Quantity:
    return nominal_strength / safety_factor


def lrfd(nominal_strength: Quantity, safety_factor: float) -> Quantity:
    return nominal_strength * safety_factor


@dataclass(frozen=True)
class Criteria:
    allowable_strength: float = 1.67
    load_resistance_factor: float = 0.9

    def design_strength(
        self, nominal_strength: Quantity, design_type: DesignType
    ):
        table: dict[
            DesignType, tuple[Callable[[Quantity, float], Quantity], float]
        ] = {
            DesignType.ASD: (asd, self.allowable_strength),
            DesignType.LRFD: (lrfd, self.load_resistance_factor),
        }
        function, factor = table[design_type]
        return function(nominal_strength, factor)


def nominal_strength(
    nominal_strengths: dict[StrengthType, Optional[Quantity]],
) -> tuple[Quantity, StrengthType]:
    strength_type, strength = min(
        filter(lambda item: item[1], nominal_strengths.items()),
        key=lambda item: item[1],
    )
    return strength, strength_type


class Strength(Protocol):
    @property
    @abstractmethod
    def nominal_strength(self) -> Quantity:
        pass

    # @property
    # @abstractmethod
    # def detailed_results(self) -> dict[str, Union[Quantity, float, None]]:
    #     return {NOMINAL_STRENGTH: self.nominal_strength}


class DesignStrengthMixin(ABC, Strength):
    @property
    @abstractmethod
    def criteria(self) -> Criteria:
        pass

    @cached_property
    def design_strength_asd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_strength, design_type=DesignType.ASD
        )

    @cached_property
    def design_strength_lrfd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_strength, design_type=DesignType.LRFD
        )

    def design_strength(self, design_criteria: DesignType):
        table = {
            DesignType.ASD: self.design_strength_asd,
            DesignType.LRFD: self.design_strength_lrfd,
        }


@dataclass(frozen=True)
class DesignStrength:
    nominal_strengths: dict[StrengthType, Strength]
    criteria: Criteria = Criteria()

    @cached_property
    def nominal_strength_tuple(self):
        return nominal_strength(
            {
                key: value.nominal_strength
                for key, value in self.nominal_strengths.items()
            }
        )

    @cached_property
    def nominal_strength(self):
        return self.nominal_strength_tuple[0]

    @cached_property
    def nominal_strength_type(self):
        return self.nominal_strength_tuple[1]

    @cached_property
    def design_strength_asd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_strength, design_type=DesignType.ASD
        )

    @cached_property
    def design_strength_lrfd(self):
        return self.criteria.design_strength(
            nominal_strength=self.nominal_strength, design_type=DesignType.LRFD
        )
