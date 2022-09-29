from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from pylatex import Quantity


class Slenderness(str, Enum):
    SLENDER = "SLENDER"
    NON_SLENDER = "NON_SLENDER"
    COMPACT = "COMPACT"
    NON_COMPACT = "NON_COMPACT"


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


@dataclass
class FlexuralSlendernessImplementation(FlexuralSlenderness):
    value: Slenderness
    slender_limit_ratio: float
    compact_limit_ratio: float


class ElementSlenderness(Protocol):
    axial_compression: AxialSlenderness
    flexural_minor_axis: FlexuralSlenderness
    flexural_major_axis: FlexuralSlenderness
    ratio: float
    area_for_shear: Quantity


class WebSlenderness(Protocol):
    web: ElementSlenderness


class FlangeWebSectionSlenderness(Protocol):
    flange: ElementSlenderness
    web: ElementSlenderness


@dataclass
class ElementSlendernessDefaultImplementation(ElementSlenderness):
    axial_compression: AxialSlenderness
    flexural_minor_axis: FlexuralSlenderness
    flexural_major_axis: FlexuralSlenderness
    ratio: float
    area_for_shear: Quantity