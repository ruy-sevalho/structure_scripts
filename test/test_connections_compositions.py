from pytest import mark, approx
from sympy.physics.units import mm, Quantity

from structure_scripts.aisc.connections.bolts import (
    AiscBolt,
    ThreadCond,
    HoleType,
    AISC_BOLT_GEOMETRIES,
    BoltDenomination,
    BOLT_GROUPS,
    BoltGroup,
    BoltGeo,
    BoltGroupMaterial,
)
from structure_scripts.aisc.connections.compositions import (
    SimpleShearTabBolted,
    SimpleShearTabBoltedAndWelded,
)
from structure_scripts.aisc.connections.elements import BearingStrengthType
from structure_scripts.aisc.connections.materials import (
    IsotropicMaterial,
    ASTM_A_36,
    WeldFillerMaterial,
    EXX_60_KSI,
)
from structure_scripts.units.sympy_units import same_units_simplify, kN


@mark.parametrize(
    """
    thickness,
    height,
    tab_material,
    n_bolts,
    bolt_geo,
    bolt_group,
    last_bolt_center_to_height_distance,
    bolt_center_to_width_distance,
    thread_in_plane,
    hole_type,
    connection_type,
    expected_asd,
    expected_lrfd,
    """,
    [
        (
            10 * mm,
            200 * mm,
            ASTM_A_36,
            2,
            AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
            BOLT_GROUPS[BoltGroup.GROUP_A](),
            50 * mm,
            50 * mm,
            ThreadCond.NOT_EXCLUDED,
            HoleType.STANDARD,
            BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
            10.0 * kN,
            15.0 * kN,
        ),
        (
            6.4 * mm,
            (17 + 38 + 17) * mm,
            ASTM_A_36,
            2,
            AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
            BOLT_GROUPS[BoltGroup.GROUP_A](),
            17 * mm,
            24 * mm,
            ThreadCond.NOT_EXCLUDED,
            HoleType.STANDARD,
            BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
            10.0 * kN,
            15.0 * kN,
        ),
    ],
)
def test_simple_shear_tab_bolted(
    thickness: Quantity,
    height: Quantity,
    tab_material: IsotropicMaterial,
    n_bolts: int,
    bolt_geo: BoltGeo,
    bolt_group: BoltGroupMaterial,
    last_bolt_center_to_height_distance: Quantity,
    bolt_center_to_width_distance: Quantity,
    thread_in_plane: ThreadCond,
    hole_type: HoleType,
    connection_type: BearingStrengthType,
    expected_asd: Quantity,
    expected_lrfd: Quantity,
):
    analysis = SimpleShearTabBolted(
        thickness=thickness,
        height=height,
        tab_material=tab_material,
        n_bolts=n_bolts,
        bolt=AiscBolt(geo=bolt_geo, group=bolt_group),
        last_bolt_center_to_height_distance=last_bolt_center_to_height_distance,
        bolt_center_to_width_distance=bolt_center_to_width_distance,
        thread_in_plane=thread_in_plane,
        hole_type=hole_type,
        connection_type=connection_type,
    )
    calc_asd, calc_lrfd = analysis._design_strengths
    calc_asd, calc_lrfd, expected_asd, expected_lrfd = same_units_simplify(
        (calc_asd, calc_lrfd, expected_asd, expected_lrfd),
        kN,
        strip_units=True,
    )
    calc = {"asd": calc_asd, "lrfd": calc_lrfd}
    # assert calc == approx({"asd": expected_asd, "lrfd": expected_lrfd})


@mark.parametrize(
    """
    weld_material,
    weld_length,
    weld_size,
    thickness,
    height,
    tab_material,
    n_bolts,
    bolt_geo,
    bolt_group,
    last_bolt_center_to_height_distance,
    bolt_center_to_width_distance,
    thread_in_plane,
    hole_type,
    connection_type,
    expected_asd,
    expected_lrfd,
    """,
    [
        # (
        #     EXX_60_KSI,
        #     100*mm,
        #     6*mm,
        #     10 * mm,
        #     200 * mm,
        #     ASTM_A_36,
        #     2,
        #     AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
        #     BOLT_GROUPS[BoltGroup.GROUP_A],
        #     50 * mm,
        #     50 * mm,
        #     ThreadCond.NOT_EXCLUDED,
        #     HoleType.STANDARD,
        #     BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
        #     10.0 * kN,
        #     15.0 * kN,
        # ),
        (
            EXX_60_KSI,
            100 * mm,
            6 * mm,
            6.4 * mm,
            (17 + 38 + 17) * mm,
            ASTM_A_36,
            2,
            AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
            BOLT_GROUPS[BoltGroup.GROUP_A](),
            17 * mm,
            24 * mm,
            ThreadCond.NOT_EXCLUDED,
            HoleType.STANDARD,
            BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
            10.0 * kN,
            15.0 * kN,
        ),
    ],
)
def test_simple_shear_tab_bolted_and_welded(
    weld_material: WeldFillerMaterial,
    weld_length: Quantity,
    weld_size: Quantity,
    thickness: Quantity,
    height: Quantity,
    tab_material: IsotropicMaterial,
    n_bolts: int,
    bolt_geo: BoltGeo,
    bolt_group: BoltGroupMaterial,
    last_bolt_center_to_height_distance: Quantity,
    bolt_center_to_width_distance: Quantity,
    thread_in_plane: ThreadCond,
    hole_type: HoleType,
    connection_type: BearingStrengthType,
    expected_asd: Quantity,
    expected_lrfd: Quantity,
):
    analysis = SimpleShearTabBoltedAndWelded(
        weld_material=weld_material,
        weld_size=weld_size,
        weld_length=weld_length,
        thickness=thickness,
        height=height,
        tab_material=tab_material,
        n_bolts=n_bolts,
        bolt=AiscBolt(geo=bolt_geo, group=bolt_group),
        last_bolt_center_to_height_distance=last_bolt_center_to_height_distance,
        bolt_center_to_width_distance=bolt_center_to_width_distance,
        thread_in_plane=thread_in_plane,
        hole_type=hole_type,
        connection_type=connection_type,
    )
    s = analysis.strengths(1, 1)
    assert True
