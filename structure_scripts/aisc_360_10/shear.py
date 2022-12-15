from dataclasses import dataclass
from functools import partial
from typing import Protocol, TYPE_CHECKING
from abc import ABC, abstractmethod

from structure_scripts.aisc_360_10.helpers import (
    _web_shear_coefficient_limit,
    web_shear_coefficient_iii,
    _nominal_shear_strength,
)

from structure_scripts.aisc_360_10.section_slenderness import (
    ElementSlendernessDefinition,
)
from structure_scripts.helpers import Axis
from structure_scripts.materials import IsotropicMaterial

if TYPE_CHECKING:
    from structure_scripts.aisc_360_10.sections import (
        SectionWithWebFlange, ConstructionType,
)

SHEAR_STRENGTH = "shear_strength"


@dataclass
class StandardShearCoefficientMixin(ABC):
    section: "SectionWithWebFlange"

    @property
    @abstractmethod
    def shear_buckling_coefficient(self) -> float:
        pass

    @property
    @abstractmethod
    def element(self) -> ElementSlendernessDefinition:
        pass

    @property
    def shear_coefficient_limit_i(self):
        return _web_shear_coefficient_limit(
            factor=1.1,
            web_shear_buckling_coefficient=self.shear_buckling_coefficient,
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def shear_coefficient_limit_ii(self):
        return _web_shear_coefficient_limit(
            factor=1.37,
            web_shear_buckling_coefficient=self.shear_buckling_coefficient,
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def shear_coefficient_iii(self):
        return web_shear_coefficient_iii(
            shear_buckling_coefficient=self.shear_buckling_coefficient,
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
            web_slenderness=self.section.slenderness.web.slenderness_ratio,
        )

    @property
    def shear_coefficient(self):
        if self.element.slenderness_ratio < self.shear_coefficient_limit_i:
            return 1.0
        elif self.element.slenderness_ratio < self.shear_coefficient_limit_ii:
            return (
                self.shear_coefficient_limit_i / self.element.slenderness_ratio
            )
        else:
            return self.shear_coefficient_iii


@dataclass
class ShearStrengthMixin(ABC):
    section: "SectionWithWebFlange"

    @property
    @abstractmethod
    def shear_coefficient(self) -> float:
        pass

    @property
    @abstractmethod
    def element(self) -> ElementSlendernessDefinition:
        pass

    @property
    def nominal_strength(self):
        return _nominal_shear_strength(
            yield_stress=self.section.material.yield_stress,
            web_area=self.element.shear_area,
            web_shear_coefficient=self.shear_coefficient,
        )


@dataclass
class StandardShearStrengthMixin(
    StandardShearCoefficientMixin, ShearStrengthMixin, ABC
):
    pass


# class ShearStrengthParam(Protocol):
#     web_slenderness_ratio: float
#     web_area: Quantity
#     web_plate_shear_buckling_coefficient: float


# @dataclass
# class ShearStrength(Criteria):
#     """ Computes shear strength criteria in accordance to
#     G2. MEMBERS WITH UNSTIFFENED OR STIFFENED WEBS
#     1. Shear Strength
#     """
#     yield_stress: Quantity
#     modulus_linear: Quantity
#     web_slenderness_ratio: float
#     web_area: Quantity
#     web_plate_shear_buckling_coefficient: float
#     rolled_i_shaped: bool = False
#     safety_factor: SafetyFactor = AllowableStrengthDesign()
#
#     # name = ""
#
#     def __post_init__(self):
#         # This code sure smells
#         if self.rolled_i_shaped:
#             if self.web_slenderness_ratio <= self.web_shear_coefficient_limit_0:
#                 self.safety_factor = deepcopy(self.safety_factor)
#                 if type(SafetyFactor) == AllowableStrengthDesign:
#                     self.safety_factor.value = 1.5
#                 elif type(SafetyFactor) == LoadAndResistanceFactorDesign:
#                     self.safety_factor.value = 1.0
#
#     @property
#     def web_shear_coefficient_limit_0(self):
#         return _web_shear_coefficient_limit(
#             factor=2.24,
#             web_shear_buckling_coefficient=1.,
#             modulus_linear=self.modulus_linear,
#             yield_stress=self.yield_stress
#         )
#
#     @property
#     def web_shear_coefficient_limit_i(self):
#         return _web_shear_coefficient_limit(
#             factor=1.1,
#             web_shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
#             modulus_linear=self.modulus_linear,
#             yield_stress=self.yield_stress
#         )
#
#     @property
#     def web_shear_coefficient_limit_ii(self):
#         return _web_shear_coefficient_limit(
#             factor=1.37,
#             web_shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
#             modulus_linear=self.modulus_linear,
#             yield_stress=self.yield_stress
#         )
#
#     @property
#     def web_shear_coefficient_iii(self):
#         return _web_shear_coefficient_iii(
#             shear_buckling_coefficient=self.web_plate_shear_buckling_coefficient,
#             modulus_linear=self.modulus_linear,
#             yield_stress=self.yield_stress,
#             web_slenderness=self.web_slenderness_ratio
#         )
#
#     @property
#     def web_shear_coefficient(self):
#         if self.web_slenderness_ratio <= self.web_shear_coefficient_limit_0:
#             return 1.0
#         if self.web_slenderness_ratio < self.web_shear_coefficient_limit_i:
#             return 1.0
#         elif self.web_slenderness_ratio < self.web_shear_coefficient_limit_ii:
#             return self.web_shear_coefficient_limit_i / self.web_slenderness_ratio
#         else:
#             return self.web_shear_coefficient_iii
#
#     @property
#     def nominal_strength(self):
#         return _nominal_shear_strength(
#             yield_stress=self.yield_stress,
#             web_area=self.web_area,
#             web_shear_coefficient=self.web_shear_coefficient,
#         )


@dataclass
class ShearStrength:
    material: IsotropicMaterial
    element: ElementSlendernessDefinition
    shear_coefficient: float

    # @property
    # def shear_coefficient_limit_0(self):
    #     return _web_shear_coefficient_limit(
    #         factor=2.24,
    #         web_shear_buckling_coefficient=1.0,
    #         modulus_linear=self.material.modulus_linear,
    #         yield_stress=self.material.yield_stress,
    #     )

    # def __post_init__(self):
    #     # This code sure smells
    #     if self.rolled_i_shaped:
    #         if self.element.slenderness_ratio <= self.shear_coefficient_limit_0:
    #             self.safety_factor = deepcopy(self.safety_factor)
    #             self.shear_coefficient = 1.0
    #             if type(self.safety_factor) == AllowableStrengthDesign:
    #                 self.safety_factor.value = 1.5
    #             elif type(self.safety_factor) == LoadAndResistanceFactorDesign:
    #                 self.safety_factor.value = 1.0

    @property
    def nominal_strength(self):
        return _nominal_shear_strength(
            yield_stress=self.material.yield_stress,
            web_area=self.element.shear_area,
            web_shear_coefficient=self.shear_coefficient,
        )


class ShearCoefficient(Protocol):
    shear_coefficient: float


class ShearBucklingCoefficient(Protocol):
    shear_buckling_coefficient: float


@dataclass
class StandardShearCoefficient:
    section: "SectionWithWebFlange"
    shear_buckling_coefficient: float
    element: ElementSlendernessDefinition

    @property
    def shear_coefficient_limit_i(self):
        return _web_shear_coefficient_limit(
            factor=1.1,
            web_shear_buckling_coefficient=self.shear_buckling_coefficient,
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def shear_coefficient_limit_ii(self):
        return _web_shear_coefficient_limit(
            factor=1.37,
            web_shear_buckling_coefficient=self.shear_buckling_coefficient,
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
        )

    @property
    def shear_coefficient_iii(self):
        return web_shear_coefficient_iii(
            shear_buckling_coefficient=self.shear_buckling_coefficient,
            modulus_linear=self.section.material.modulus_linear,
            yield_stress=self.section.material.yield_stress,
            web_slenderness=self.section.slenderness.web.slenderness_ratio,
        )

    @property
    def shear_coefficient(self):
        if self.element.slenderness_ratio < self.shear_coefficient_limit_i:
            return 1.0
        elif self.element.slenderness_ratio < self.shear_coefficient_limit_ii:
            return (
                self.shear_coefficient_limit_i / self.element.slenderness_ratio
            )
        else:
            return self.shear_coefficient_iii


# @dataclass
# class ShearStrengthElementAdaptor:
#     beam: "BeamAnalysis"
#     element: ElementSlendernessDefinition
#     shear_coefficient: float
#
#     @property
#     def rolled_i_shaped(self):
#         return self.beam.section.construction == ConstructionType.ROLLED and type(self.beam.section) in [
#             DoublySymmetricI,
#         ]
#
#     @property
#     def shear_coefficient_limit_0(self):
#         return _web_shear_coefficient_limit(
#             factor=2.24,
#             web_shear_buckling_coefficient=1.,
#             modulus_linear=self.beam.section.material.modulus_linear,
#             yield_stress=self.beam.section.material.yield_stress
#         )
#
#     def __post_init__(self):
#         # This code sure smells
#         self.safety_factor = self.beam.safety_factor
#         if self.rolled_i_shaped:
#             if self.element.slenderness_ratio <= self.shear_coefficient_limit_0:
#                 self.safety_factor = deepcopy(self.beam.safety_factor)
#                 self.shear_coefficient = 1.0
#                 if type(SafetyFactor) == AllowableStrengthDesign:
#                     self.safety_factor.value = 1.5
#                 elif type(SafetyFactor) == LoadAndResistanceFactorDesign:
#                     self.safety_factor.value = 1.0
#
#     @property
#     def criteria(self):
#         return ShearStrength(
#             material=self.beam.section.material,
#             element=self.element,
#             safety_factor=self.safety_factor
#         )


@dataclass
class DefaultWebShearCoefficientCalcMemory:
    web_shear_coefficient_limit_i: float
    web_shear_coefficient_limit_ii: float
    web_shear_coefficient_limit_iii: float
    web_shear_coefficient: float


@dataclass
class StandardShearCriteriaAdaptor:
    section: "SectionWithWebFlange"
    # beam: "Beam"
    axis: Axis

    name = SHEAR_STRENGTH

    @property
    def rolled(self):
        return self.section.construction == ConstructionType.ROLLED and type(
            self.section
        ).__name__ in [
            "DoublySymmetricI",
        ]

    @property
    def shear_buckling_coefficient(self):
        table = {
            Axis.MAJOR: 5,
            Axis.MINOR: 1.2,
        }
        return table[self.axis]

    @property
    def element(self):
        table = {
            Axis.MAJOR: self.section.slenderness.web,
            Axis.MINOR: self.section.slenderness.flange,
        }
        return table[self.axis]

    @property
    def shear_coefficient_model(self):
        return StandardShearCoefficient(
            section=self.section,
            shear_buckling_coefficient=self.shear_buckling_coefficient,
            element=self.element,
        )

    @property
    def nominal_strength(self):
        return ShearStrength(
            element=self.element,
            material=self.section.material,
            shear_coefficient=self.shear_coefficient_model.shear_coefficient,
        )


StandardShearMajorAxisCriteriaAdaptor = partial(
    StandardShearCriteriaAdaptor, axis=Axis.MAJOR
)
StandardShearMajorAxisCriteriaAdaptor = partial(
    StandardShearCriteriaAdaptor, axis=Axis.MINOR
)

# @dataclass
# class ShearStrength(Criteria):
#     """ Computes shear strength criteria in accordance to
#     G2. MEMBERS WITH UNSTIFFENED OR STIFFENED WEBS
#     1. Shear Strength
#     """
#     material: IsotropicMaterial
#     element: ElementSlendernessDefinition
#     plate_shear_buckling_coefficient: float
#     rolled_i_shaped: bool = False
#     safety_factor: SafetyFactor = AllowableStrengthDesign()
#
#     def __post_init__(self):
#         # This code sure smells
#         if self.rolled_i_shaped:
#             if self.element.slenderness_ratio <= self.shear_coefficient_limit_0:
#                 self.safety_factor = deepcopy(self.safety_factor)
#                 if type(SafetyFactor) == AllowableStrengthDesign:
#                     self.safety_factor.value = 1.5
#                 elif type(SafetyFactor) == LoadAndResistanceFactorDesign:
#                     self.safety_factor.value = 1.0
#
#     @property
#     def shear_coefficient_limit_0(self):
#         return _web_shear_coefficient_limit(
#             factor=2.24,
#             web_shear_buckling_coefficient=1.,
#             modulus_linear=self.material.modulus_linear,
#             yield_stress=self.material.yield_stress
#         )
#
#     @property
#     def shear_coefficient_limit_i(self):
#         return _web_shear_coefficient_limit(
#             factor=1.1,
#             web_shear_buckling_coefficient=self.plate_shear_buckling_coefficient,
#             modulus_linear=self.material.modulus_linear,
#             yield_stress=self.material.yield_stress
#         )
#
#     @property
#     def shear_coefficient_limit_ii(self):
#         return _web_shear_coefficient_limit(
#             factor=1.37,
#             web_shear_buckling_coefficient=self.plate_shear_buckling_coefficient,
#             modulus_linear=self.material.modulus_linear,
#             yield_stress=self.material.yield_stress
#         )
#
#     @property
#     def shear_coefficient_iii(self):
#         return _web_shear_coefficient_iii(
#             shear_buckling_coefficient=self.plate_shear_buckling_coefficient,
#             modulus_linear=self.material.modulus_linear,
#             yield_stress=self.material.yield_stress,
#             web_slenderness=self.element.slenderness_ratio
#         )
#
#     @property
#     def shear_coefficient(self):
#         if self.element.slenderness_ratio <= self.shear_coefficient_limit_0:
#             return 1.0
#         if self.element.slenderness_ratio < self.shear_coefficient_limit_i:
#             return 1.0
#         elif self.element.slenderness_ratio < self.shear_coefficient_limit_ii:
#             return self.shear_coefficient_limit_i / self.element.slenderness_ratio
#         else:
#             return self.shear_coefficient_iii
#
#     @property
#     def nominal_strength(self):
#         return _nominal_shear_strength(
#             yield_stress=self.material.yield_stress,
#             web_area=self.element.shear_area,
#             web_shear_coefficient=self.shear_coefficient,
#         )


# @dataclass
# class ShearMajorAxisAdaptor(ShearStrengthElementAdaptor):
#     @property
#     def element(self) -> ElementSlendernessDefinition:
#         return self.beam.section.slenderness.web
#
#     @property
#     def plate_shear_buckling_coefficient(self) -> float:
#         return


# @dataclass
# class ShearMinorAxisAdaptor:
#     profile: SectionWithWebAndFlange
#     safety_factor: SafetyFactor = AllowableStrengthDesign()
#
#     @property
#     def criteria(self):
#         return ShearStrength(
#             yield_stress=self.profile.material.yield_stress,
#             modulus_linear=self.profile.material.modulus_linear,
#             web_slenderness_ratio=self.profile.slenderness.flange.slenderness_ratio,
#             web_area=self.profile.slenderness.flange.shear_area,
#             web_plate_shear_buckling_coefficient=1.2,
#             rolled_i_shaped=False,
#             safety_factor=self.safety_factor
#         )

#
# @dataclass
# class ShearStrengthAdaptor:
#     model: "BeamAnalysis"
