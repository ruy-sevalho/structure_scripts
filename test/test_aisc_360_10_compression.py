from dataclasses import asdict

from pytest import mark

from structure_scripts.aisc.compression import BeamCompression
from structure_scripts.aisc.criteria import (
    StrengthType,
)

from structure_scripts.aisc.aisc_database import AISC_Sections
from structure_scripts.materials import (
    IsotropicMaterial,
    steel250MPa,
)
from structure_scripts.aisc.sections import ConstructionType, AISC_Section
from structure_scripts.aisc.profile import create_profile

from test.helpers import (
    compare_loading_strengths,
    ExpectedDesignStrength,
)
from quantities import N, MPa, m

test_params = {
    "test_1": (
        AISC_Sections["W6X15"],
        steel250MPa,
        BeamCompression(length_major_axis=2.1 * m),
        ConstructionType.ROLLED,
        ExpectedDesignStrength(
            design_strength_asd=360263.2504 * N,
            design_strength_lrfd=541475.6653 * N,
            nominal_strength=601639.6281 * N,
            nominal_strength_type=StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS,
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: {
                    "elastic_buckling_stress": 1891.114675 * MPa,
                    "buckling_critical_stress": 236.5429382 * MPa,
                    "nominal_strength": 676512.8032 * N,
                },
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: {
                    "elastic_buckling_stress": 606.1593226 * MPa,
                    "buckling_critical_stress": 210.3635063 * MPa,
                    "nominal_strength": 601639.6281 * N,
                },
                StrengthType.TORSIONAL_BUCKLING: {
                    "elastic_buckling_stress": 776.5846487 * MPa,
                    "buckling_critical_stress": 218.4856161 * MPa,
                    "nominal_strength": 624868.862 * N,
                },
            },
        ),
    ),
    "test_2": (
        AISC_Sections["C4X4.5"],
        steel250MPa,
        BeamCompression(length_major_axis=1.4 * m),
        ConstructionType.ROLLED,
        ExpectedDesignStrength(
            design_strength_asd=57393.14831 * N,
            design_strength_lrfd=86261.9019 * N,
            nominal_strength=95846.55767 * N,
            nominal_strength_type=StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS,
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: {
                    "elastic_buckling_stress": 1701.207597 * MPa,
                    "buckling_critical_stress": 235.0863958 * MPa,
                    "nominal_strength": 203349.7324 * N,
                },
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: {
                    "elastic_buckling_stress": 128.5969169 * MPa,
                    "buckling_critical_stress": 110.805269 * MPa,
                    "nominal_strength": 95846.55767 * N,
                },
                StrengthType.TORSIONAL_BUCKLING: {
                    "elastic_buckling_stress": 494.3621679 * MPa,
                    "buckling_critical_stress": 202.3095837 * MPa,
                    "nominal_strength": 174997.7899 * N,
                },
            },
        ),
    ),
}


@mark.parametrize(
    "section, material, beam_param, construction_type, expected",
    test_params.values(),
    ids=test_params.keys(),
)
def test_compression(
    section: AISC_Section,
    material: IsotropicMaterial,
    beam_param: BeamCompression,
    construction_type: ConstructionType,
    expected: ExpectedDesignStrength,
):
    analysis = create_profile(
        section=section, material=material, construction=construction_type
    )
    compression = analysis.compression(**asdict(beam_param))
    calc, exp = compare_loading_strengths(compression, expected)
    assert calc == exp
