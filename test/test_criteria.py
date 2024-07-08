from functools import lru_cache

from pytest import mark
from quantities import Quantity, N

from structure_scripts.aisc.criteria import Criteria, DesignType
from test.helpers import same_units_dictionary_simplify_for_test_assert


@mark.parametrize(
    "nominal_strength, asd_factor, lrfd_factor, expected_asd_str, expected_lrfd_str",
    [(100 * N, 2, 0.9, 50 * N, 90 * N)],
)
def test_criteria(
    nominal_strength: Quantity,
    asd_factor: float,
    lrfd_factor: float,
    expected_asd_str: Quantity,
    expected_lrfd_str: Quantity,
):
    criteria = Criteria(
        allowable_strength=asd_factor, load_resistance_factor=lrfd_factor
    )
    calc = {
        DesignType.ASD: criteria.design_strength(nominal_strength, DesignType.ASD),
        DesignType.LRFD: criteria.design_strength(nominal_strength, DesignType.LRFD),
    }
    exp = {
        DesignType.ASD: expected_asd_str,
        DesignType.LRFD: expected_lrfd_str,
    }
    calc, exp = same_units_dictionary_simplify_for_test_assert(calc, exp)
    assert calc == exp
