import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from quantities import Quantity


class DesignType(str, Enum):
    ASD = "ASD"
    LRFD = "LRFD"


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


def design_strength(
    nominal_strength: Quantity,
    design_type: DesignType,
    design_type_factors: dict[DesignType, float],
):
    def asd(nominal_strength: Quantity, safety_factor: float) -> Quantity:
        return nominal_strength / safety_factor

    def lrfd(nominal_strength: Quantity, safety_factor: float) -> Quantity:
        return nominal_strength * safety_factor

    table = {
        DesignType.ASD: asd,
        DesignType.LRFD: lrfd,
    }
    return table[design_type](
        nominal_strength=nominal_strength,
        safety_factor=design_type_factors[design_type],
    )


def default_design_type_factors():
    return {
        DesignType.ASD: 1.67,
        DesignType.LRFD: 0.9,
    }


class NominalStrengthModel(Protocol):
    @abc.abstractmethod
    @property
    def nominal_strength(self) -> Quantity:
        pass

    @abc.abstractmethod
    @property
    def valid(self) -> True:
        pass


@dataclass
class Criteria:
    strength_models: dict[str, NominalStrengthModel]
    design_type_factors: dict[DesignType, float]
    design_type: DesignType

    @property
    def design_strength(self) -> tuple[Quantity, str]:
        d = self.strength_models
        nominal_strength_key = min(
            (key for key in self.strength_models if d[key].valid),
            key=lambda key: d[key].nominal_strength,
        )
        return (
            design_strength(
                nominal_strength=self.strength_models[
                    nominal_strength_key
                ].nominal_strength,
                design_type=self.design_type,
                design_type_factors=self.design_type_factors,
            ),
            nominal_strength_key,
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
