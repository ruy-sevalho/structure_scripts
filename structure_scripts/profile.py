from typing import Union, Type, Callable

from structure_scripts.aisc_360_10.channel import ChannelAISC36010
from structure_scripts.aisc_360_10.i_profile import DoublySymmetricIAISC36010
from structure_scripts.aisc_360_10.sections import AISC_360_10_Rule_Check
from structure_scripts.materials import IsotropicMaterial
from structure_scripts.section import AISC_Section, SectionType
from structure_scripts.section_properties import ConstructionType


def create_profile(
    section: AISC_Section,
    material: IsotropicMaterial,
    construction: ConstructionType = ConstructionType.ROLLED,
) -> AISC_360_10_Rule_Check:

    table = {
        SectionType.W: DoublySymmetricIAISC36010,
        SectionType.C: ChannelAISC36010,
    }
    # noinspection PyArgumentList
    return table[section.type](
        section=section, material=material, construction=construction
    )
