from pytest import mark, approx

# from quantities import Quantity, mm, MPa, N
from sympy.physics.units.quantities import Quantity
from sympy.physics.units import mm, N
from pandas import DataFrame

from structure_scripts.aisc.connections.elements import TensionDistribution, BlockShearStrength, TensileYield, \
    TensileRupture
from structure_scripts.aisc.criteria import DesignType
from structure_scripts.units.sympy_units import MPa, kN, same_units_simplify
from structure_scripts.aisc.connections.bolts import (
    BoltSpacing,
    check_bolt_minimum_spacing,
    BoltCombinedTensionAndShear, BOLT_TENSILE_STRENGTH, BOLT_SHEAR_STRENGTH, BearingStrengthType,
    BoltHolesBearingStrength,
)
from structure_scripts.aisc.connections.bolts import BoltStrength


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
    "nominal_body_area, nominal_stress, expected_nominal_strength",
    [
        (10.0 * mm**2, 250.0 * MPa, 2500.0 * N),
    ],
)
def test_bolt_strength(
    nominal_body_area: Quantity,
    nominal_stress: Quantity,
    expected_nominal_strength: Quantity,
):
    criteria = BoltStrength(Ab=nominal_body_area, Fn=nominal_stress)
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
            0.0
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
        Ab=nominal_body_area,
        Fnt=nominal_tensile_stress,
        Fnv=nominal_shear_stress,
    )
    # calc, exp = same_units_simplify(
    #     criteria.nominal_strength, expected_nominal_strength, unit=kN
    # )
    calc = criteria.rule_check(
        required_shear_strength=required_shear_strength,
        required_tensile_strength=required_tensile_strength,
        design_criteria=design_criteria,
    )
    calc = calc[BOLT_TENSILE_STRENGTH][0], calc[BOLT_SHEAR_STRENGTH][0]
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
        (400.*MPa, 25.*mm, 25.*mm, 10.*mm, BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED, 120.*kN),
        (400.*MPa, 25.*mm, 25.*mm, 10.*mm, BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED, 150.*kN),
        (400.*MPa, 25.*mm, 25.*mm, 12.*mm, BearingStrengthType.LONG_SLOTTED_LOAD_PERPENDICULAR_TO_SLOT, 120.*kN),
        (400.*MPa, 25.*mm, 25.*mm, 8.*mm, BearingStrengthType.LONG_SLOTTED_LOAD_PERPENDICULAR_TO_SLOT, 80.*kN)
    ]
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
        Fu=tensile_str,
        d=bolt_diameter,
        lc=clear_distance,
        t=thickness,
        connection_type=connection_type
    ).nominal_strength
    calc, exp = same_units_simplify((bearing_str, exp_str), kN)
    assert calc == approx(exp)


@mark.parametrize(
    "Fy, Ag, str_asd, str_lrfd",
    [
        (250*MPa, 50*mm**2, 7485.02994*N, 11250.*N)
    ]
)
def test_tension_yield(Fy: Quantity, Ag: Quantity, str_asd: Quantity, str_lrfd: Quantity):
    tension_yield = TensileYield(Fy=Fy, Ag=Ag)
    calc_asd, calc_lrfd = tension_yield.design_strength_asd, tension_yield.design_strength_lrfd
    calc_asd, calc_lrfd, str_asd, str_lrfd = same_units_simplify((calc_asd, calc_lrfd, str_asd, str_lrfd), kN, strip_units=True)
    calc = {"asd": calc_asd, "lrfd": calc_lrfd}
    assert calc == approx({"asd": str_asd, "lrfd": str_lrfd})


@mark.parametrize(
    "Fu, Ae, str_asd, str_lrfd",
    [
        (400*MPa, 50*mm**2, 10000.*N, 15000.*N)
    ]
)
def test_tension_rupture(Fu: Quantity, Ae: Quantity, str_asd: Quantity, str_lrfd: Quantity):
    tension_yield = TensileRupture(Fu=Fu, Ae=Ae)
    calc_asd, calc_lrfd = tension_yield.design_strength_asd, tension_yield.design_strength_lrfd
    calc_asd, calc_lrfd, str_asd, str_lrfd = same_units_simplify((calc_asd, calc_lrfd, str_asd, str_lrfd), kN, strip_units=True)
    calc = {"asd": calc_asd, "lrfd": calc_lrfd}
    assert calc == approx({"asd": str_asd, "lrfd": str_lrfd})


@mark.parametrize(
    "Fy, Fu, Anv, Ant, Agv, Agt, Ubs, expected_str",
    [
        (250*MPa, 400*MPa, 90*mm**2, 90*mm**2, 100*mm**2, 100*mm**2, TensionDistribution.NON_UNIFORM, 33.*kN)
    ]
)
def test_block_shear(
    Fy: Quantity,
    Fu: Quantity,
    Anv: Quantity,
    Ant: Quantity,
    Agv: Quantity,
    Agt: Quantity,
    Ubs: TensionDistribution,
    expected_str: Quantity
):
    block_shear = BlockShearStrength(
        Fy=Fy, Fu=Fu, Anv=Anv, Ant=Ant, Agv=Agv, Agt=Agt, Ubs=Ubs
    ).nominal_strength
    calc, exp = same_units_simplify((block_shear, expected_str), kN)
    assert calc == approx(exp)
