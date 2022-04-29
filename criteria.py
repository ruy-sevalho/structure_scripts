from dataclasses import dataclass
from enum import Enum
from functools import total_ordering, cached_property
from quantities import Quantity
from helpers import same_units_simplify


class SafetyFactorType(str, Enum):
    ASD = "ASD"
    LRFD = "LRFD"


@dataclass(frozen=True)
class SafetyFactor:
    theoretical_limit_value: Quantity
    safety_factor: float
    type_: SafetyFactorType

    @cached_property
    def allowable_value(self) -> Quantity:
        table = {
            SafetyFactorType.ASD: self.theoretical_limit_value / self.safety_factor,
            SafetyFactorType.LRFD: self.theoretical_limit_value * self.safety_factor
        }
        return table[self.type_]


@dataclass
@total_ordering
class Criteria:
    calculated_value: Quantity
    safety_factor: SafetyFactor

    def __post_init__(self) -> None:
        q1, q2 = same_units_simplify(self.calculated_value, self.safety_factor.theoretical_limit_value)
        self.calculated_value = q1
        self.calculated_value = q2

    @cached_property
    def passed(self):
        if self.calculated_value < self.safety_factor.allowable_value:
            return True
        return False

    @cached_property
    def ratio(self):
        ratio = self.safety_factor.allowable_value / self.calculated_value
        # Since ths is allowable/calculated value for design purposes, the real concern is for ratios<1
        # The cutoff is there so big numbers don't clutter the report
        # if ratio > 10:
        #     ratio = ">10"
        return ratio

    def __eq__(self, other: "Criteria"):
        if self.ratio == other.ratio:
            return True
        return False

    def __lt__(self, other: "Criteria"):
        if self.ratio < other.ratio:
            return True
        return False

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
