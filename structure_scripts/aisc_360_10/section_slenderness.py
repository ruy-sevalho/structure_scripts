from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Protocol
from abc import abstractmethod

from pylatex import Quantity


SLENDERNESS_RATIO = "slenderness_ratio"
SLENDERNESS_LIMIT = "slenderness_limit"
SLENDERNESS_COMPACT_NON_COMPACT_LIMIT = "slenderness_compact_non_compact_limit"
SLENDERNESS_NON_COMPACT_SLENDER_LIMIT = "slenderness_non_compact_slender_limit"


class Slenderness(str, Enum):
    SLENDER = "slender"
    NON_SLENDER = "non_slender"
    COMPACT = "compact"
    NON_COMPACT = "non_compact"


def flexural_slenderness_per_element(
    limit_slender: float, limit_compact: float, ratio: float
) -> Slenderness:
    if ratio < limit_compact:
        return Slenderness.COMPACT
    elif ratio < limit_slender:
        return Slenderness.NON_COMPACT
    else:
        return Slenderness.SLENDER


def axial_slenderness_per_element(slenderness: float, limit: float):
    if slenderness < limit:
        return Slenderness.NON_SLENDER
    return Slenderness.SLENDER


@dataclass(frozen=True)
class AxialSlendernessCalcMemory:
    ratio: float
    slender_limit: float
    value: Slenderness


@dataclass(frozen=True)
class FlexuralSlendernessCalcMemory:
    ratio: float
    compact_non_compact_limit: float
    non_compact_slender_limit: float
    value: Slenderness


@dataclass(frozen=True)
class DoublySymmetricIAndChannelSlenderness:
    web_axial: Slenderness
    web_flexure_major_axis: Slenderness
    flange_axial: Slenderness
    flange_flexure_major_axis: Slenderness
    flange_flexure_minor_axis: Slenderness


# @dataclass
# class DoublySymmetricIAndChannelWebSlendernessCalcMemory:
#     axial: AxialSlendernessCalcMemory
#     flexure_major_axis: FlexuralSlendernessCalcMemory
#
#
# @dataclass
# class DoublySymmetricIAndChannelFlangeSlendernessCalcMemory:
#     axial: AxialSlendernessCalcMemory
#     flexure_major_axis: FlexuralSlendernessCalcMemory
#     flexure_minor_axis: FlexuralSlendernessCalcMemory


@dataclass(frozen=True)
class DoublySymmetricIAndChannelAxialCalcMemory:
    web: AxialSlendernessCalcMemory
    flange: AxialSlendernessCalcMemory


@dataclass(frozen=True)
class DoublySymmetricIAndChannelFlexureMajorAxisCalcMemory:
    web: FlexuralSlendernessCalcMemory
    flange: FlexuralSlendernessCalcMemory


@dataclass(frozen=True)
class DoublySymmetricIAndChannelFlexureMinorAxisCalcMemory:
    flange: FlexuralSlendernessCalcMemory


@dataclass(frozen=True)
class DoublySymmetricIAndChannelSlendernessCalcMemory:
    axial: DoublySymmetricIAndChannelAxialCalcMemory
    flexure_major_axis: DoublySymmetricIAndChannelFlexureMajorAxisCalcMemory
    flexure_minor_axis: DoublySymmetricIAndChannelFlexureMinorAxisCalcMemory


# @dataclass
# class DoublySymmetricIAndChannelSlenderness:
#     axial:
#     flexure_major_axis:
#     flexure_minor_axis:

# class ElementSlenderness(Protocol):
#     @property
#     @abstractmethod
#     def axial_limit(self) -> float:
#         pass
#
#     @property
#     @abstractmethod
#     def axial_limit(self) -> float:
#         pass


# class AxialSlenderness(Protocol):
#     value: Slenderness
#     limit_ratio: float
#
#
# @dataclass
# class AxialSlendernessImplementation(AxialSlenderness):
#     value: Slenderness
#     limit_ratio: float
#
#
# class FlexuralSlenderness(Protocol):
#     value: Slenderness
#     slender_limit_ratio: float
#     compact_limit_ratio: float
#
#
# class ElementSlendernessDefinition(Protocol):
#     slenderness_ratio: float
#     shear_area: Quantity
#
#
# class ElementSlendernessLimits(Protocol):
#     axial_compression: AxialSlenderness
#     flexural_minor_axis: FlexuralSlenderness
#     flexural_major_axis: FlexuralSlenderness
#
#
# class ElementSlenderness(
#     ElementSlendernessDefinition, ElementSlendernessLimits, Protocol
# ):
#     ...


# @dataclass
# class AxialSlendernessCompute(AxialSlenderness):
#     limit_ratio: float
#     slenderness_ratio: float
#
#     @cached_property
#     def value(self) -> Slenderness:
#         limit = self.limit_ratio
#         ratio = self.slenderness_ratio
#         if ratio < limit:
#             return Slenderness.NON_SLENDER
#         return Slenderness.SLENDER


# @dataclass
# class FlexuralSlendernessCompute(FlexuralSlenderness):
#     compact_limit_ratio: float
#     slender_limit_ratio: float
#     slenderness_ratio: float
#
#     @cached_property
#     def value(self):
#         return flexural_slenderness_per_element(
#             limit_slender=self.slender_limit_ratio,
#             limit_compact=self.compact_limit_ratio,
#             ratio=self.slenderness_ratio,
#         )
#
#
# class WebSlenderness(Protocol):
#     web: ElementSlenderness


# class FlangeWebSlenderness(Protocol):
#     flange: ElementSlenderness
#     web: ElementSlenderness

#
# @dataclass(frozen=True)
# class FlangeWebSlenderness:
#     pass
