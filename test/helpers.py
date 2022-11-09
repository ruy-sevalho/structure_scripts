from dataclasses import dataclass
from functools import partial
from typing import Any, Optional, Union

from pytest import approx
from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    LoadingStrength,
    StrengthType,
    DesignStrength,
    NOMINAL_STRENGTH,
)
from structure_scripts.helpers import same_units_simplify


def same_units_dictionary_simplify(
    d1: dict[str, Quantity | float | StrengthType | str],
    d2: dict[str, Quantity | float | StrengthType | str],
    rel: float = None,
    abs: float = None,
    nan_ok: bool = False,
    strip_units=True,
) -> tuple[dict[str, str | float], dict[str, str | float]]:
    if not d1.keys() == d2.keys():
        raise ValueError("d1 and d2 don't have the same keys")
    for key in d1:
        if not type(d1[key]) == type(d2[key]):
            raise ValueError(
                f"d1[{key}] = {d1[key]} and d2[{key}] = {d2[key]} are not of the same type"
            )
        if isinstance(d1[key], Quantity):
            d1[key], d2[key] = same_units_simplify(
                d1[key], d2[key], strip_units=strip_units
            )
        if isinstance(d1[key], float):
            partial_approx = partial(approx, rel=rel, abs=abs, nan_ok=nan_ok)
            d2[key] = partial_approx(d2[key])
        if isinstance(d1[key], StrengthType):
            d1[key], d2[key] = d1[key].value, d2[key].value
    return d1, d2


def convert_loading_strength(
    results: DesignStrength,
) -> dict[str, Quantity | float]:
    """Converts a Loading Strength result into a flat dict format, to be used in assertion statements."""
    flatten_nominal_strengths = {
        f"{outer_key.value}_{inner_key}": inner_value
        for outer_key, outer_value in results.nominal_strengths.items()
        for inner_key, inner_value in outer_value.detailed_results.items()
    }
    return {
        **flatten_nominal_strengths,
        NOMINAL_STRENGTH: results.nominal_strength,
        "nominal_strength_type": results.nominal_strength_type,
        "design_strength_asd": results.design_strength_asd,
        "design_strength_lrfd": results.design_strength_lrfd,
    }


@dataclass(frozen=True)
class ExpectedDesignStrength:
    nominal_strengths: dict[
        StrengthType, dict[str, dict[str, Union[Quantity, float, None]]]
    ]
    nominal_strength: Quantity
    nominal_strength_type: StrengthType
    design_strength_asd: Quantity
    design_strength_lrfd: Quantity


def _flatten_expected_design_strength(expected: ExpectedDesignStrength):
    flattened_nominal_strengths = {
        f"{outer_key.value}_{inner_key}": inner_value
        for outer_key, outer_value in expected.nominal_strengths.items()
        for inner_key, inner_value in outer_value.items()
    }
    return {
        **flattened_nominal_strengths,
        "nominal_strength": expected.nominal_strength,
        "nominal_strength_type": expected.nominal_strength_type,
        "design_strength_asd": expected.design_strength_asd,
        "design_strength_lrfd": expected.design_strength_lrfd,
    }


def compare_loading_strengths(
    calculated: DesignStrength,
    expected: ExpectedDesignStrength,
    rel: Any = None,
    abs: Any = None,
    nan_ok: bool = False,
):
    flattened_calculated = convert_loading_strength(calculated)
    flattened_expected = _flatten_expected_design_strength(expected)
    processed_calculated, processed_expected = same_units_dictionary_simplify(
        flattened_calculated,
        flattened_expected,
        abs=abs,
        rel=rel,
        nan_ok=nan_ok,
    )
    return processed_calculated, processed_expected
