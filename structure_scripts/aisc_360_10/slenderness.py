from dataclasses import dataclass
from typing import Protocol

from structure_scripts.aisc_360_10.helpers import Slenderness


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


class WebSlenderness(Protocol):
    web: ElementSlenderness


class FlangeWebSectionSlenderness(Protocol):
    flange: ElementSlenderness
    web: ElementSlenderness