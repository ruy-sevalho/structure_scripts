from enum import Enum

from quantities import Quantity

from structure_scripts.helpers import ratio_simplify

BOLT_SPACING_RATIO_ACCEPTED = 8/3
BOLT_SPACING_RATIO_PREFERRED = 3


class BoltSpacing(str, Enum):
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    PREFERRED = "PREFERRED"


def check_bolt_minimun_spacing(nominal_diameter: Quantity, spacing: Quantity) -> BoltSpacing:
    ratio = ratio_simplify(spacing, nominal_diameter)
    if ratio > BOLT_SPACING_RATIO_PREFERRED:
        return BoltSpacing.PREFERRED
    if ratio > BOLT_SPACING_RATIO_ACCEPTED:
        return BoltSpacing.ACCEPTED
    return BoltSpacing.REJECTED
