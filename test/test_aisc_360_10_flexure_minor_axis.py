from pytest import mark

from structure_scripts.aisc.aisc_database import AISC_Sections
from structure_scripts.aisc.criteria import (
    StrengthType,
    NOMINAL_STRENGTH,
)
from structure_scripts.aisc.sections import ConstructionType, AISC_Section
from structure_scripts.aisc.profile import create_profile
from structure_scripts.materials import steel250MPa, IsotropicMaterial

from test.helpers import (
    compare_loading_strengths,
    ExpectedDesignStrength,
)
from quantities import N, mm


test_params = {
    "test_1": (
        AISC_Sections["W6X15"],
        steel250MPa,
        ConstructionType.ROLLED,
        ExpectedDesignStrength(
            design_strength_asd=11376451.76 * N * mm,
            design_strength_lrfd=17098806.99 * N * mm,
            nominal_strength=18998674.43 * N * mm,
            nominal_strength_type=StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING,
            nominal_strengths={
                StrengthType.YIELD: {
                    "nominal_strength": 19450000 * N * mm,
                },
                StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING: {
                    NOMINAL_STRENGTH: 18998674.43 * N * mm
                },
            },
        ),
    ),
    "test_2": (
        AISC_Sections["C4X4.5"],
        steel250MPa,
        ConstructionType.ROLLED,
        ExpectedDesignStrength(
            design_strength_asd=994011.976 * N * mm,
            design_strength_lrfd=1494000 * N * mm,
            nominal_strength=1660000 * N * mm,
            nominal_strength_type=StrengthType.YIELD,
            nominal_strengths={
                StrengthType.YIELD: {
                    "nominal_strength": 1660000 * N * mm,
                },
            },
        ),
    ),
}


@mark.parametrize(
    "section, material, construction, expected",
    test_params.values(),
    ids=test_params.keys(),
)
def test_flexure_minor_axis(
    section: AISC_Section,
    material: IsotropicMaterial,
    construction: ConstructionType,
    expected: ExpectedDesignStrength,
):
    profile = create_profile(
        section=section, material=material, construction=construction
    )
    flexure = profile.flexure_minor_axis()
    calc, exp = compare_loading_strengths(flexure, expected)
    assert calc == exp
