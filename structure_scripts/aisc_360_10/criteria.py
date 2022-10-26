from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Callable

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


# class SafetyFactor(Protocol):
#     value: float
#
#     def allowable_value(self, theoretical_limit_value: Quantity) -> Quantity:
#         ...
#
#     def ratio(
#         self, theoretical_limit_value: Quantity, required_value
#     ) -> Quantity:
#         return abs(
#             required_value / self.allowable_value(theoretical_limit_value)
#         )
#
#
# @dataclass
# class AllowableStrengthDesign(SafetyFactor):
#     value: float = 1.67
#
#     def allowable_value(self, theoretical_limit_value: Quantity) -> Quantity:
#         return theoretical_limit_value / self.value
#
#
# @dataclass
# class LoadAndResistanceFactorDesign(SafetyFactor):
#     value: float = 0.90
#
#     def allowable_value(self, theoretical_limit_value: Quantity) -> Quantity:
#         return theoretical_limit_value * self.value


def asd(nominal_strength: Quantity, safety_factor: float) -> Quantity:
    return nominal_strength / safety_factor


def lrfd(nominal_strength: Quantity, safety_factor: float) -> Quantity:
    return nominal_strength * safety_factor


@dataclass
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


class DesignStrength(Protocol):
    @property
    @abstractmethod
    def nominal_strength(self) -> Quantity:
        pass

    @property
    @abstractmethod
    def design_strength(self) -> Quantity:
        pass

    @property
    @abstractmethod
    def strength_type(self) -> StrengthType:
        pass


# class StrengthCollection(Protocol):
#     @property
#     @abc.abstractmethod
#     def values(self) -> dict[str, Quantity]:
#         ...


class DesignStrengthMixin(ABC):
    criteria: Criteria = Criteria()
    design_type: DesignType = DesignType.ASD

    @property
    @abstractmethod
    def strengths(self) -> dict[str, Quantity]:
        pass

    @property
    def design_strength(self) -> tuple[Quantity, str]:
        return min(
            (
                (
                    self.criteria.design_strength(item[1], self.design_type),
                    item[0],
                )
                for item in self.strengths.items()
                if item[1]
            ),
            key=lambda x: x[1],
        )

# class Criteria(Protocol):
#     @property
#     def valid(self) -> bool:
#         return True
#
#     @property
#     def nominal_strength(self) -> Quantity:
#         ...
#
#     @property
#     def design_strength(self):
#         return design_strength(
#             nominal_strength=self.nominal_strength,
#             safety_factor=self.design_type_factors[self.design_type],
#         )
#
#     @property
#     def aux_parameters(self) -> dict[str, Quantity | float] | None:
#         return None


# class DesignStrength:
#     nominal_strength: Quantity
#     design_type: DesignType
#     design_type_factors: dict[DesignType, float] = {
#         DesignType.ASD: 1.67,
#         DesignType.LRFD: 0.9,
#     }
#
#     @property
#     def design_strength(self):
#         return design_strength(
#             nominal_strength=self.nominal_strength,
#             safety_factor=self.design_type_factors[self.design_type],
#         )


# class CriteriaAdaptor(Criteria, Protocol):
#     @property
#     def criteria(self) -> Criteria:
#         ...

#     @property
#     def nominal_strength(self):
#         return self.criteria.nominal_strength

#     @property
#     def design_strength(self):
#         return self.criteria.design_strength

#     @property
#     def aux_parameters(self) -> dict[str, Quantity | float] | None:
#         return self.criteria.aux_parameters

#     @property
#     def safety_factor(self):
#         return self.criteria.design_type


# @dataclass
# class CriteriaCollection:
#     criteria_dict: dict[str, Criteria]

#     @property
#     def design_strength_criteria(self) -> tuple[Criteria, str]:
#         return min(
#             (x for x in self.criteria_dict.values() if x.valid),
#             key=lambda x: x.design_strength,
#         )

#     @property
#     def nominal_strength(self) -> Quantity:
#         return min(
#             (x for x in self.criteria_dict.values() if x.valid),
#             key=lambda x: x.nominal_strength,
#         ).nominal_strength


# @dataclass
# class DesignStrength:
#     theoretical_limit_value: Quantity
#     safety_factor: SafetyFactor
#
#     @property
#     def allowable_value(self) -> Quantity:
#         return self.safety_factor.allowable_value(self.theoretical_limit_value)


# @dataclass
# @total_ordering
# class Criteria:
#     calculated_value: Quantity
#     safety_factor: DesignStrength
#
#     def __post_init__(self) -> None:
#         q1, q2 = same_units_simplify(self.calculated_value, self.safety_factor.theoretical_limit_value)
#         self.calculated_value = q1
#         self.calculated_value = q2
#
#     @property
#     def passed(self):
#         if self.calculated_value < self.safety_factor.allowable_value:
#             return True
#         return False
#
#     @property
#     def ratio(self):
#         ratio = self.safety_factor.allowable_value / self.calculated_value
#         # Since ths is allowable/calculated value for design purposes, the real concern is for ratios<1
#         # The cutoff is there so big numbers don't clutter the report
#         # if ratio > 10:
#         #     ratio = ">10"
#         return ratio
#
#     def __eq__(self, other: "Criteria"):
#         if self.ratio == other.ratio:
#             return True
#         return False
#
#     def __lt__(self, other: "Criteria"):
#         if self.ratio < other.ratio:
#             return True
#         return False

# def to_latex(self, round_precision: int = 2):
#     ratio = self.ratio
#     if ratio > 10:
#         return ">10"
#     print_ratio = Quantity(
#         Quantity(ratio), options={"round-precision": round_precision}
#     )
#     if ratio < 1:
#         print_ratio = Command(
#             "textcolor", arguments="red", extra_arguments=print_ratio
#         )
#     return print_ratio
