from pytest import mark

from structure_scripts.aisc_360_10.i_profile import DoublySymmetricIAISC36010
from structure_scripts.section_slenderness import (
    DoublySymmetricIAndChannelSlenderness,
    Slenderness,
)
from structure_scripts.aisc_database import AISC_Sections
from structure_scripts.materials import steel355MPa, IsotropicMaterial
from structure_scripts.section_properties import ConstructionType

slenderness_test_data = [
    (
        AISC_Sections["W6X15"],
        steel355MPa,
        ConstructionType.ROLLED,
        DoublySymmetricIAndChannelSlenderness(
            web_axial=Slenderness.NON_SLENDER,
            web_flexure_major_axis=Slenderness.COMPACT,
            flange_axial=Slenderness.NON_SLENDER,
            flange_flexure_major_axis=Slenderness.NON_COMPACT,
            flange_flexure_minor_axis=Slenderness.NON_COMPACT,
        ),
    )
]


@mark.parametrize(
    "section, material, construction, slenderness", slenderness_test_data
)
def test_slenderness(
    section: AISC_Sections,
    material: IsotropicMaterial,
    construction: ConstructionType,
    slenderness: DoublySymmetricIAndChannelSlenderness,
):
    assert (
        DoublySymmetricIAISC36010(
            material=material, section=section, construction=construction
        ).slenderness
        == slenderness
    )
