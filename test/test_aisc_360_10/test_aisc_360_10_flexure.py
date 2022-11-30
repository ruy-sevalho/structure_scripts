from dataclasses import asdict

from pytest import mark


from structure_scripts.aisc_360_10.criteria import (
    StrengthType,
)
from structure_scripts.aisc_360_10.flexure import BeamFlexure
from structure_scripts.aisc_360_10.sections import AISC_360_10_Rule_Check

from test.data import (
    sections,
)
from test.helpers import (
    compare_loading_strengths,
    ExpectedDesignStrength,
)
from quantities import Quantity, cm, N, MPa, m, mm

beam_params = {
    "beam_01": BeamFlexure(length=1.0 * m),
    "beam_02": BeamFlexure(length=2.0 * m),
    "beam_04": BeamFlexure(length=4.0 * m),
    "beam_005": BeamFlexure(length=0.5 * m),
}

flexure_major_axis = {
    "w_127x127x73x13": {
        "beam_005": ExpectedDesignStrength(
            design_strength_asd=17856287.43 * N * mm,
            design_strength_lrfd=26838000 * N * mm,
            nominal_strength=29820000 * N * mm,
            nominal_strength_type=StrengthType.YIELD,
            nominal_strengths={
                StrengthType.YIELD: {
                    "nominal_strength": 29820000 * N * mm,
                },
                StrengthType.LATERAL_TORSIONAL_BUCKLING: {
                    "limit_length_yield": 769.6008355 * mm,
                    "limit_length_torsional_buckling": 2912.384214 * mm,
                    "nominal_strength": None,
                },
            },
        ),
        "beam_01": ExpectedDesignStrength(
            design_strength_asd=17136299.74 * N * mm,
            design_strength_lrfd=25755858.51 * N * mm,
            nominal_strength=28617620.57 * N * mm,
            nominal_strength_type=StrengthType.LATERAL_TORSIONAL_BUCKLING,
            nominal_strengths={
                StrengthType.YIELD: {
                    "nominal_strength": 29820000 * N * mm,
                },
                StrengthType.LATERAL_TORSIONAL_BUCKLING: {
                    "limit_length_yield": 769.6008355 * mm,
                    "limit_length_torsional_buckling": 2912.384214 * mm,
                    "nominal_strength": 28617620.57 * N * mm,
                },
            },
        ),
        "beam_04": ExpectedDesignStrength(
            design_strength_asd=7779382.274 * N * mm,
            design_strength_lrfd=11692411.56 * N * mm,
            nominal_strength=12991568.4 * N * mm,
            nominal_strength_type=StrengthType.LATERAL_TORSIONAL_BUCKLING,
            nominal_strengths={
                StrengthType.YIELD: {
                    "nominal_strength": 29820000 * N * mm,
                },
                StrengthType.LATERAL_TORSIONAL_BUCKLING: {
                    "limit_length_yield": 769.6008355 * mm,
                    "limit_length_torsional_buckling": 2912.384214 * mm,
                    "nominal_strength": 12991568.4 * N * mm,
                },
            },
        ),
    }
}


flexure_major_axis_test_inputs = [
    (sections[key1].aisc_360_10, asdict(beam_params[key2]), value2)
    for key1, value1 in flexure_major_axis.items()
    for key2, value2 in value1.items()
]


@mark.parametrize(
    "section, beam_param, expected",
    flexure_major_axis_test_inputs,
)
def test_flexure_major_axis(
    section: AISC_360_10_Rule_Check,
    beam_param: dict[str, Quantity | float],
    expected: ExpectedDesignStrength,
):
    flexure = section.flexure_major_axis(**beam_param)
    calc, exp = compare_loading_strengths(flexure, expected)
    assert calc == exp
