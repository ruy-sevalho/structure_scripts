from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from quantities import Quantity


class SafetyFactorType(str, Enum):
    ASD = "ASD"
    LRFD = "LRFD"


class SafetyFactor(Protocol):
    value: float
    
    def allowable_value(self, theoretical_limit_value: Quantity) -> Quantity:
        ...

    def ratio(self, theoretical_limit_value: Quantity, required_value) -> Quantity:
        return abs(required_value / self.allowable_value(theoretical_limit_value))


@dataclass
class AllowableStrengthDesign(SafetyFactor):
    value: float = 1.67

    def allowable_value(self, theoretical_limit_value: Quantity) -> Quantity:
        return theoretical_limit_value / self.value


@dataclass
class LoadAndResistanceFactorDesign(SafetyFactor):
    value: float = 0.90

    def allowable_value(self, theoretical_limit_value: Quantity) -> Quantity:
        return theoretical_limit_value * self.value


class Criteria(Protocol):
    safety_factor: SafetyFactor
    name: str

    @property
    def valid(self) -> bool:
        return True

    @property
    def nominal_strength(self) -> Quantity:
        ...

    @property
    def design_strength(self):
        return self.safety_factor.allowable_value(self.nominal_strength)

    @property
    def aux_parameters(self) -> dict[str, Quantity | float] | None:
        return None


class CriteriaAdaptor(Criteria, Protocol):
    name: str

    @property
    def criteria(self) -> Criteria:
        ...

    @property
    def nominal_strength(self):
        return self.criteria.nominal_strength

    @property
    def design_strength(self):
        return self.criteria.design_strength

    @property
    def aux_parameters(self) -> dict[str, Quantity | float] | None:
        return self.criteria.aux_parameters

    @property
    def safety_factor(self):
        return self.criteria.safety_factor

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


