from dataclasses import asdict

from pytest import mark

from structure_scripts.aisc.aisc_database import AISC_Sections
from structure_scripts.aisc.criteria import (
    StrengthType,
    NOMINAL_STRENGTH,
)
from structure_scripts.aisc.flexure import BeamFlexure
from structure_scripts.aisc.sections import ConstructionType, AISC_Section
from structure_scripts.aisc.profile import create_profile
from structure_scripts.materials import steel250MPa, IsotropicMaterial

from test.helpers import (
    compare_loading_strengths,
    ExpectedDesignStrength,
)
from quantities import N, m, mm


test_params = {
    "test_1": (
        AISC_Sections["W6X15"],
        steel250MPa,
        BeamFlexure(length=2.1 * m),
        ConstructionType.ROLLED,
        ExpectedDesignStrength(
            design_strength_asd=25927091.62 * N * mm,
            design_strength_lrfd=38968418.71 * N * mm,
            nominal_strength=43298243.01 * N * mm,
            nominal_strength_type=StrengthType.LATERAL_TORSIONAL_BUCKLING,
            nominal_strengths={
                StrengthType.YIELD: {
                    "nominal_strength": 44250000 * N * mm,
                },
                StrengthType.LATERAL_TORSIONAL_BUCKLING: {
                    "limit_length_yield": 1831.91568 * mm,
                    "limit_length_torsional_buckling": 6458.39598 * mm,
                    "nominal_strength": 43298243.01 * N * mm,
                },
                StrengthType.COMPRESSION_FLANGE_LOCAL_BUCKLING: {
                    NOMINAL_STRENGTH: 43545674.83 * N * mm
                },
            },
        ),
    )
}


@mark.parametrize(
    "section, material, beam_param, construction, expected",
    test_params.values(),
    ids=test_params.keys(),
)
def test_flexure_major_axis(
    section: AISC_Section,
    material: IsotropicMaterial,
    beam_param: BeamFlexure,
    construction: ConstructionType,
    expected: ExpectedDesignStrength,
):
    profile = create_profile(
        section=section, material=material, construction=construction
    )
    flexure = profile.flexure_major_axis(**asdict(beam_param))
    calc, exp = compare_loading_strengths(flexure, expected)
    assert calc == exp
