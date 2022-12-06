from dataclasses import asdict

from pytest import mark

from structure_scripts.aisc_360_10.compression import BeamCompression
from structure_scripts.aisc_360_10.criteria import (
    StrengthType,
)
from structure_scripts.aisc_360_10.sections import AISC_360_10_Rule_Check

from test.data import (
    sections,
)
from test.helpers import (
    compare_loading_strengths,
    ExpectedDesignStrength,
)
from quantities import Quantity, cm, N, MPa, m

beam_params = {
    "beam_01": BeamCompression(length_major_axis=1 * m),
    "beam_02": BeamCompression(length_major_axis=2 * m),
    "beam_04": BeamCompression(length_major_axis=4 * m),
}

compression = {
    "w_127x127x73x13": {
        "beam_01": ExpectedDesignStrength(
            design_strength_asd=280978.8249 * N,
            design_strength_lrfd=422311.1739 * N,
            nominal_strength=469234.6376 * N,
            nominal_strength_type=StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS,
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: {
                    "elastic_buckling_stress": 5658.57319 * MPa,
                    "buckling_critical_stress": 345.7995726 * MPa,
                    "nominal_strength": 570569.2948 * N,
                },
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: {
                    "elastic_buckling_stress": 669.9367836 * MPa,
                    "buckling_critical_stress": 284.3846289 * MPa,
                    "nominal_strength": 469234.6376 * N,
                },
                StrengthType.TORSIONAL_BUCKLING: {
                    "elastic_buckling_stress": 1161.123206 * MPa,
                    "buckling_critical_stress": 312.35827874 * MPa,
                    "nominal_strength": 5153.91159926 * cm**2 * MPa,
                },
            },
        ),
        "beam_02": ExpectedDesignStrength(
            design_strength_asd=144446.4555 * N,
            design_strength_lrfd=217103.0226 * N,
            nominal_strength=241225.5807 * N,
            nominal_strength_type=StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS,
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: {
                    "elastic_buckling_stress": 1414.643297 * MPa,
                    "buckling_critical_stress": 319.6043999 * MPa,
                    "nominal_strength": 527347.2599 * N,
                },
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: {
                    "elastic_buckling_stress": 167.4841959 * MPa,
                    "buckling_critical_stress": 146.1973216 * MPa,
                    "nominal_strength": 241225.5807 * N,
                },
                StrengthType.TORSIONAL_BUCKLING: {
                    "elastic_buckling_stress": 601.4102911 * MPa,
                    "buckling_critical_stress": 277.2878718 * MPa,
                    "nominal_strength": 457524.9885 * N,
                },
            },
        ),
        "beam_04": ExpectedDesignStrength(
            design_strength_asd=36281.13857 * N,
            design_strength_lrfd=54530.55128 * N,
            nominal_strength=60589.50142 * N,
            nominal_strength_type=StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS,
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: {
                    "elastic_buckling_stress": 353.6608244 * MPa,
                    "buckling_critical_stress": 233.2200795 * MPa,
                    "nominal_strength": 384813.1311 * N,
                },
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: {
                    "elastic_buckling_stress": 41.87104897 * MPa,
                    "buckling_critical_stress": 36.72090995 * MPa,
                    "nominal_strength": 60589.50142 * N,
                },
                StrengthType.TORSIONAL_BUCKLING: {
                    "elastic_buckling_stress": 461.4820624 * MPa,
                    "buckling_critical_stress": 257.2744642 * MPa,
                    "nominal_strength": 424502.8659 * N,
                },
            },
        ),

    },
    "channel_6_inch_8dot2_lb_ft": {
        "beam_1400_mm": ExpectedDesignStrength(
            design_strength_asd=280978.8249 * N,
            design_strength_lrfd=422311.1739 * N,
            nominal_strength=469234.6376 * N,
            nominal_strength_type=StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS,
            nominal_strengths={
                StrengthType.FLEXURAL_BUCKLING_MAJOR_AXIS: {
                    "elastic_buckling_stress": 5658.57319 * MPa,
                    "buckling_critical_stress": 345.7995726 * MPa,
                    "nominal_strength": 570569.2948 * N,
                },
                StrengthType.FLEXURAL_BUCKLING_MINOR_AXIS: {
                    "elastic_buckling_stress": 669.9367836 * MPa,
                    "buckling_critical_stress": 284.3846289 * MPa,
                    "nominal_strength": 469234.6376 * N,
                },
                StrengthType.TORSIONAL_BUCKLING: {
                    "elastic_buckling_stress": 1161.123206 * MPa,
                    "buckling_critical_stress": 312.35827874 * MPa,
                    "nominal_strength": 5153.91159926 * cm**2 * MPa,
                },
            },
        ),
    }
}
compression_test_inputs = [
    (sections[key1].aisc_360_10, asdict(beam_params[key2]), value2)
    for key1, value1 in compression.items()
    for key2, value2 in value1.items()
]


@mark.parametrize(
    "section, beam_param, expected",
    compression_test_inputs,
)
def test_compression(
    section: AISC_360_10_Rule_Check,
    beam_param: dict[str, Quantity | float],
    expected: ExpectedDesignStrength,
):
    compression = section.compression(**beam_param)
    calc, exp = compare_loading_strengths(compression, expected)
    assert calc == exp
