from quantities import inch
from sympy.physics.units import mm, convert_to, degree

from examples.proje101.critical_loads import w
from structure_scripts.aisc.connections.bolts import (
    AISC_BOLT_GEOMETRIES,
    BoltDenomination,
    BoltGroup,
    BOLT_GROUPS,
    ThreadCond,
    HoleType,
    AiscBolt,
)
from structure_scripts.aisc.connections.compositions import (
    SimpleShearTabBolted,
    SimpleShearTabBoltedAndWelded,
    TensionTab,
    TensionTabMomentConnection,
    BasePlateBolts,
    BasePlateWeld,
    WeldSide,
)
from structure_scripts.aisc.connections.elements import BearingStrengthType
from structure_scripts.aisc.connections.materials import (
    ASTM_A_36,
    EXX_60_KSI,
    EXX_70_KSI,
)

connections_criteria = {
    "long": (
        SimpleShearTabBoltedAndWelded(
            weld_material=EXX_70_KSI,
            weld_length=128 * mm,
            weld_size=6 * mm,
            thickness=6.4 * mm,
            height=(17 + 38 + 17) * mm,
            tab_material=ASTM_A_36,
            n_bolts=2,
            bolt=AiscBolt(
                AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
                BOLT_GROUPS[BoltGroup.GROUP_A],
            ),
            last_bolt_center_to_height_distance=17 * mm,
            bolt_center_to_width_distance=24 * mm,
            thread_in_plane=ThreadCond.NOT_EXCLUDED,
            hole_type=HoleType.STANDARD,
            connection_type=BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
        ),
        TensionTabMomentConnection(
            dist_between_tabs=152 * mm,
            bolt=AiscBolt(
                AISC_BOLT_GEOMETRIES[BoltDenomination.IMP5_8],
                BOLT_GROUPS[BoltGroup.GROUP_A],
            ),
            n_bolts_per_row=2,
            distance_first_hole_center_to_edge=25 * mm,
            distance_between_bolt_center_in_row=50 * mm,
            tab_material=ASTM_A_36,
            tab_width=50 * mm,
            tab_thickness=3.0 / 8.0 * 25.4 * mm,
            thread_in_plane=ThreadCond.NOT_EXCLUDED,
            connection_type=BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED,
            # weld_length=100 * mm,
            # weld_size=6 * mm,
            # filler_material=EXX_70_KSI,
            # theta=0 * degree,
        ),
    ),
    "trans": SimpleShearTabBoltedAndWelded(
        weld_material=EXX_70_KSI,
        weld_length=55.0 * mm,
        weld_size=6.0 * mm,
        thickness=6.4 * mm,
        height=55.0 * mm,
        tab_material=ASTM_A_36,
        n_bolts=1,
        bolt=AiscBolt(
            AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
            BOLT_GROUPS[BoltGroup.GROUP_A],
        ),
        last_bolt_center_to_height_distance=55 / 2.0 * mm,
        bolt_center_to_width_distance=29.0 * mm,
        thread_in_plane=ThreadCond.NOT_EXCLUDED,
        hole_type=HoleType.STANDARD,
        connection_type=BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED,
    ),
    "platform_diag": TensionTab(
        tab_thickness=0.25 * 25.4 * mm,
        tab_width=50 * mm,
        tab_material=ASTM_A_36,
        bolt=AiscBolt(
            AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
            BOLT_GROUPS[BoltGroup.GROUP_A],
        ),
        n_bolts_per_row=2,
        n_bolts_row=1,
        distance_first_hole_center_to_edge=17 * mm,
        distance_between_bolt_center_in_row=38 * mm,
        weld_size=6 * mm,
        weld_length=100 * mm,
        filler_material=EXX_70_KSI,
    ),
    "column_base": (
        BasePlateBolts(
            dim_y_hole=225 * mm,
            dim_z_hole=225 * mm,
            dim_y_col=49 * mm,
            dim_z_col=150 * mm,
            bolt=AiscBolt(
                AISC_BOLT_GEOMETRIES[BoltDenomination.IMP1_2],
                BOLT_GROUPS[BoltGroup.GROUP_A],
            ),
        ),
        BasePlateWeld(
            i_section=w.section,
            flanges_size=8 * mm,
            web_size=8 * mm,
            flanges_type=WeldSide.SINGLE,
            web_type=WeldSide.SINGLE,
        ),
    ),
}

if __name__ == "__main__":
    trans = connections_criteria["trans"]
    trans_ds = trans.strengths()
