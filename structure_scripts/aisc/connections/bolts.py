import math
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from sympy import pi
from sympy.physics.units import Quantity, inch, convert_to, mm

from structure_scripts.units.sympy_units import MPa, kN


class ThreadCond(str, Enum):
    NOT_EXCLUDED = "not_excluded"
    EXCLUDED = "excluded"


class HoleType(str, Enum):
    STANDARD = "standard"
    OVERSIZE = "oversize"


class BoltGroup(str,Enum):
    GROUP_A = "group_a"
    GROUP_B = "group_b"


@dataclass
class BoltGroupMaterial:
    nominal_tensile_strength: Quantity
    nominal_shear_strength_threaded: Quantity
    nominal_shear_not_threaded: Quantity

    def nominal_shear_strength(self, thread_condition: ThreadCond):
        table = {
            ThreadCond.NOT_EXCLUDED: self.nominal_shear_strength_threaded,
            ThreadCond.EXCLUDED: self.nominal_shear_not_threaded
        }
        return table[thread_condition]


# Table J3.2  Nominal Strength of Fasteners and Threaded Parts
BOLT_GROUPS = {
    BoltGroup.GROUP_A: BoltGroupMaterial(
        nominal_shear_strength_threaded=372 * MPa,
        nominal_shear_not_threaded=457 * MPa,
        nominal_tensile_strength=620 * MPa,
    )
}


@dataclass
class BoltGeo:
    nominal_dia: Quantity
    standard_hole_dia: Quantity
    oversize_hole_dia: Quantity
    short_slot_width: Quantity
    short_slot_length: Quantity
    long_slot_width: Quantity
    long_slot_length: Quantity

    @cached_property
    def area(self) -> Quantity:
        return self.nominal_dia**2 * math.pi / 4

    def hole_dia(self, hole_type: HoleType) -> Quantity:
        table = {
            HoleType.STANDARD: self.standard_hole_dia,
            HoleType.OVERSIZE: self.oversize_hole_dia
        }
        return table[hole_type]

    @classmethod
    def new_convert_to_mm(
        cls,
        **kwargs
    ) -> "BoltGeo":
        return cls(
            **{key: convert_to(value, mm) for key, value in kwargs.items()}
        )

class BoltDenomination(str, Enum):
    M16 = "M16"
    M20 = "M20"
    M22 = "M22"
    M24 = "M24"
    IMP1_2 = "1/2"
    IMP5_8 = "5/8"


def _convert_to_mm(q: Quantity) -> Quantity:
    return convert_to(q, mm)


# Table J3.3 Nominal Hole Dimensions
AISC_BOLT_GEOMETRIES = {
    BoltDenomination.IMP1_2: BoltGeo.new_convert_to_mm(
        nominal_dia=1 / 2 * inch,
        standard_hole_dia=9 / 16 * inch,
        oversize_hole_dia=5 / 8 * inch,
        short_slot_width=9 / 16 * inch,
        short_slot_length=11 / 16 * inch,
        long_slot_width=9 / 16 * inch,
        long_slot_length=(1 + 1 / 4) * inch,
    )
}


@dataclass
class AiscBolt:
    geo: BoltGeo
    group: BoltGroupMaterial = BOLT_GROUPS[BoltGroup.GROUP_A]


if __name__ == "__main__":
    b = AiscBolt(
        geo=AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
    )


kN