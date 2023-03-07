from pytest import mark, approx

# from quantities import Quantity, mm, MPa, N
from sympy import pi
from sympy.physics.units.quantities import Quantity
from sympy.physics.units import mm, N, degree, radian, radians, m
from pandas import DataFrame

from structure_scripts.aisc.connections.elements import (
    TensionDistribution,
    BlockShearStrength,
    TensileYield,
    TensileRupture, BoltHolesBearingStrength, BearingStrengthType,
)
from structure_scripts.aisc.connections.welds import FilletWeld
from structure_scripts.aisc.criteria import DesignType
from structure_scripts.units.sympy_units import MPa, kN, same_units_simplify
from structure_scripts.aisc.connections.bolt_criteria import (
    BoltSpacing,
    check_bolt_minimum_spacing,
    BoltCombinedTensionAndShear,
    BOLT_TENSILE_STRENGTH,
    BOLT_SHEAR_STRENGTH,
)
from structure_scripts.aisc.connections.bolt_criteria import BoltStrength


@mark.parametrize(
    "nominal_diameter, spacing, expected_criteria",
    [
        (10.0 * mm, 10.0 * mm, BoltSpacing.REJECTED),
        (10.0 * mm, 29.0 * mm, BoltSpacing.ACCEPTED),
        (10.0 * mm, 35.0 * mm, BoltSpacing.PREFERRED),
    ],
)
def test_minimum_spacing(
    nominal_diameter: Quantity,
    spacing: Quantity,
    expected_criteria: BoltSpacing,
):
    assert (
        check_bolt_minimum_spacing(nominal_diameter, spacing)
        == expected_criteria
    )


@mark.parametrize(
    "nominal_body_area, nominal_stress, n_bolts, expected_nominal_strength",
    [
        (10.0 * mm**2, 250.0 * MPa, 1, 2500.0 * N),
        (10.0 * mm**2, 250.0 * MPa, 2, 5000.0 * N),
    ],
)
def test_bolt_strength(
    nominal_body_area: Quantity,
    nominal_stress: Quantity,
    n_bolts: int,
    expected_nominal_strength: Quantity,
):
    criteria = BoltStrength(
        nominal_body_area=nominal_body_area, nominal_stress=nominal_stress, n_bolts=n_bolts
    )
    calc, exp = same_units_simplify(
        (criteria.nominal_strength, expected_nominal_strength), unit=kN
    )
    assert calc == approx(exp)


@mark.parametrize(
    """nominal_body_area, 
    nominal_tensile_stress, 
    nominal_shear_stress, 
    required_tensile_strength,
    required_shear_strength,
    design_criteria,
    tensile_ratio,
    shear_ratio
    """,
    [
        (
            10.0 * mm**2,
            250.0 * MPa,
            250.0 * MPa,
            100.0 * N,
            100.0 * N,
            DesignType.ASD,
            0.08,
            0.08,
        ),
        (
            10.0 * mm**2,
            250.0 * MPa,
            250.0 * MPa,
            100.0 * N,
            100.0 * N,
            DesignType.LRFD,
            0.053333333,
            0.053333333,
        ),
        (
            10.0 * mm**2,
            250.0 * MPa,
            250.0 * MPa,
            1250.0 * N,
            0.0 * N,
            DesignType.LRFD,
            0.666666667,
            0.0,
        ),
    ],
)
def test_bolt_combined_shear_and_tensile_strength(
    nominal_body_area: Quantity,
    nominal_tensile_stress: Quantity,
    nominal_shear_stress: Quantity,
    required_tensile_strength: Quantity,
    required_shear_strength: Quantity,
    design_criteria: DesignType,
    tensile_ratio: float,
    shear_ratio: float,
):
    criteria = BoltCombinedTensionAndShear(
        nominal_body_area=nominal_body_area,
        nominal_tensile_stress=nominal_tensile_stress,
        nominal_shear_stress=nominal_shear_stress,
    )
    # calc, exp = same_units_simplify(
    #     criteria.nominal_strength, expected_nominal_strength, unit=kN
    # )
    calc = criteria.rule_check(
        required_shear_strength_=required_shear_strength,
        required_tensile_strength_=required_tensile_strength,
        design_criteria=design_criteria,
    )
    calc = calc[BOLT_TENSILE_STRENGTH], calc[BOLT_SHEAR_STRENGTH]
    assert calc == approx((tensile_ratio, shear_ratio))


@mark.parametrize(
    """
    tensile_str,
    bolt_diameter,
    clear_distance,
    thickness,
    connection_type,
    exp_str
    """,
    [
        (
            400.0 * MPa,
            25.0 * mm,
            25.0 * mm,
            10.0 * mm,
            BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED,
            120.0 * kN,
        ),
        (
            400.0 * MPa,
            25.0 * mm,
            25.0 * mm,
            10.0 * mm,
            BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
            150.0 * kN,
        ),
        (
            400.0 * MPa,
            25.0 * mm,
            25.0 * mm,
            12.0 * mm,
            BearingStrengthType.LONG_SLOTTED_LOAD_PERPENDICULAR_TO_SLOT,
            120.0 * kN,
        ),
        (
            400.0 * MPa,
            25.0 * mm,
            25.0 * mm,
            8.0 * mm,
            BearingStrengthType.LONG_SLOTTED_LOAD_PERPENDICULAR_TO_SLOT,
            80.0 * kN,
        ),
    ],
)
def test_bearing_strength(
    tensile_str: Quantity,
    bolt_diameter: Quantity,
    clear_distance: Quantity,
    thickness: Quantity,
    connection_type: BearingStrengthType,
    exp_str: Quantity,
):
    bearing_str = BoltHolesBearingStrength(
        ultimate_stress=tensile_str,
        bolt_diameter=bolt_diameter,
        clear_distance=clear_distance,
        thickness=thickness,
        connection_type=connection_type,
    ).nominal_strength
    calc, exp = same_units_simplify((bearing_str, exp_str), kN)
    assert calc == approx(exp)


@mark.parametrize(
    "yield_stress, gross_area, str_asd, str_lrfd",
    [(250 * MPa, 50 * mm**2, 7485.02994 * N, 11250.0 * N)],
)
def test_tension_yield(
    yield_stress: Quantity,
    gross_area: Quantity,
    str_asd: Quantity,
    str_lrfd: Quantity,
):
    tension_yield = TensileYield(yield_stress=yield_stress, gross_area=gross_area)
    calc_asd, calc_lrfd = (
        tension_yield.design_strength_asd,
        tension_yield.design_strength_lrfd,
    )
    calc_asd, calc_lrfd, str_asd, str_lrfd = same_units_simplify(
        (calc_asd, calc_lrfd, str_asd, str_lrfd), kN, strip_units=True
    )
    calc = {"asd": calc_asd, "lrfd": calc_lrfd}
    assert calc == approx({"asd": str_asd, "lrfd": str_lrfd})


@mark.parametrize(
    "ultimate_stress, net_area, str_asd, str_lrfd",
    [(400 * MPa, 50 * mm**2, 10000.0 * N, 15000.0 * N)],
)
def test_tension_rupture(
    ultimate_stress: Quantity,
    net_area: Quantity,
    str_asd: Quantity,
    str_lrfd: Quantity,
):
    tension_yield = TensileRupture(
        ultimate_stress=ultimate_stress, net_area=net_area
    )
    calc_asd, calc_lrfd = (
        tension_yield.design_strength_asd,
        tension_yield.design_strength_lrfd,
    )
    calc_asd, calc_lrfd, str_asd, str_lrfd = same_units_simplify(
        (calc_asd, calc_lrfd, str_asd, str_lrfd), kN, strip_units=True
    )
    calc = {"asd": calc_asd, "lrfd": calc_lrfd}
    assert calc == approx({"asd": str_asd, "lrfd": str_lrfd})


@mark.parametrize(
    """
    yield_stress, 
    ultimate_stress, 
    net_shear_area, 
    net_tension_area, 
    gross_shear_area, 
    tension_distribution_factor, 
    expected_str
    """,
    [
        (
            250 * MPa,
            400 * MPa,
            90 * mm**2,
            90 * mm**2,
            100 * mm**2,
            TensionDistribution.NON_UNIFORM,
            33.0 * kN,
        )
    ],
)
def test_block_shear(
    yield_stress: Quantity,
    ultimate_stress: Quantity,
    net_shear_area: Quantity,
    net_tension_area: Quantity,
    gross_shear_area: Quantity,
    tension_distribution_factor: TensionDistribution,
    expected_str: Quantity,
):
    block_shear = BlockShearStrength(
        yield_stress=yield_stress,
        ultimate_stress=ultimate_stress,
        net_shear_area=net_shear_area,
        net_tension_area=net_tension_area,
        gross_shear_area=gross_shear_area,
        tension_distribution_factor=tension_distribution_factor,
    ).nominal_strength
    calc, exp = same_units_simplify((block_shear, expected_str), kN)
    assert calc == approx(exp)


@mark.parametrize(
    "filler_metal_strength, weld_size, weld_length, theta, exp_asd, exp_lrfd",
    [
        (
            500 * MPa,
            6 * mm,
            50 * mm,
            90 * degree,
            47729.70773 * N,
            71594.5616 * N,
        ),
        (500 * MPa, 6 * mm, 50 * mm, pi / 2, 47729.70773 * N, 71594.5616 * N),
        (
            500 * MPa,
            6 * mm,
            50 * mm,
            0 * degree,
            31819.80515 * N,
            47729.70773 * N,
        ),
        (
            500 * MPa,
            6 * mm,
            50 * mm,
            45 * degree,
            41279.88982 * N,
            61919.83474 * N,
        ),
    ],
)
def test_fillet_weld(
    filler_metal_strength: Quantity,
    weld_size: Quantity,
    weld_length: Quantity,
    theta: Quantity,
    exp_asd: Quantity,
    exp_lrfd: Quantity,
):
    weld = FilletWeld(
        filler_metal_strength=filler_metal_strength,
        weld_size=weld_size,
        weld_length=weld_length,
        theta=theta,
    )
    calc_asd, calc_lrfd = weld.design_strength(DesignType.ASD), weld.design_strength(DesignType.LRFD)
    calc_asd, calc_lrfd, str_asd, str_lrfd = same_units_simplify(
        (calc_asd, calc_lrfd, exp_asd, exp_lrfd), kN, strip_units=True
    )
    calc = {"asd": calc_asd, "lrfd": calc_lrfd}
    assert calc == approx({"asd": str_asd, "lrfd": str_lrfd})
