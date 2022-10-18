from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Protocol

from pylatex import Quantity


class Slenderness(str, Enum):
    SLENDER = "SLENDER"
    NON_SLENDER = "NON_SLENDER"
    COMPACT = "COMPACT"
    NON_COMPACT = "NON_COMPACT"


def _flexural_slenderness_per_element(limit_slender: float, limit_compact: float, ratio: float) -> "Slenderness":
    if ratio < limit_compact:
        return Slenderness.COMPACT
    elif ratio < limit_slender:
        return Slenderness.NON_COMPACT
    else:
        return Slenderness.SLENDER


class AxialSlenderness(Protocol):
    value: Slenderness
    limit_ratio: float


@dataclass
class AxialSlendernessImplementation(AxialSlenderness):
    value: Slenderness
    limit_ratio: float


class FlexuralSlenderness(Protocol):
    value: Slenderness
    slender_limit_ratio: float
    compact_limit_ratio: float


class ElementSlendernessDefinition(Protocol):
    slenderness_ratio: float
    shear_area: Quantity


class ElementSlendernessLimits(Protocol):
    axial_compression: AxialSlenderness
    flexural_minor_axis: FlexuralSlenderness
    flexural_major_axis: FlexuralSlenderness


class ElementSlenderness(ElementSlendernessDefinition, ElementSlendernessLimits, Protocol):
    ...


@dataclass
class AxialSlendernessCompute(AxialSlenderness):
    limit_ratio: float
    slenderness_ratio: float

    @cached_property
    def value(self) -> Slenderness:
        limit = self.limit_ratio
        ratio = self.slenderness_ratio
        if ratio < limit:
            return Slenderness.NON_SLENDER
        return Slenderness.SLENDER


@dataclass
class FlexuralSlendernessCompute(FlexuralSlenderness):
    compact_limit_ratio: float
    slender_limit_ratio: float
    slenderness_ratio: float

    @cached_property
    def value(self):
        return _flexural_slenderness_per_element(
            limit_slender=self.slender_limit_ratio,
            limit_compact=self.compact_limit_ratio,
            ratio=self.slenderness_ratio
        )


class WebSlenderness(Protocol):
    web: ElementSlenderness


class FlangeWebSlenderness(Protocol):
    flange: ElementSlenderness
    web: ElementSlenderness
