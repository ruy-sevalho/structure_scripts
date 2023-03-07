from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from math import sqrt
from typing import Protocol, Callable, runtime_checkable
from abc import abstractmethod, ABC
from pandas import DataFrame, Series
from sympy import solve
from sympy.physics.units import Quantity, convert_to, N, degree, mm

from structure_scripts.aisc.connections.bolt_criteria import (
    BoltStrength,
    BoltCombinedTensionAndShear,
    BOLT_TENSILE_STRENGTH,
    BOLT_SHEAR_STRENGTH,
)
from structure_scripts.aisc.connections.bolts import (
    AiscBolt,
    ThreadCond,
    HoleType,
)
from structure_scripts.aisc.connections.elements import (
    ShearYield,
    ShearRupture,
    BoltHolesBearingStrength,
    BoltHolesBearingStrengthMultiple,
    BearingStrengthType,
    BlockShearStrength,
    TensionDistribution,
    TensileYield,
    TensileRupture,
)
from structure_scripts.aisc.connections.materials import (
    IsotropicMaterial,
    WeldFillerMaterial,
    EXX_70_KSI,
)
from structure_scripts.aisc.connections.welds import (
    FilletWeld,
    FilletWeldDirectStress,
    WELD_STRENGTH,
)
from structure_scripts.aisc.criteria import (
    DesignType,
    DesignStrengths,
    DesignStrengthMixin,
)
from structure_scripts.aisc.sections import AISC_Section
from structure_scripts.process_external_files.ansys import SZ, FX, MY, MZ, SY
from structure_scripts.symbols.symbols import (
    force1,
    dim_z_col,
    dim_z_hol,
    force2,
    column_axial_load,
    dim_y_col,
    dim_y_hol,
    moment_y,
    moment_z,
)
from structure_scripts.units.sympy_units import kN, ratio_simplify, MPa

BOLT_SHEAR = "bolt_shear"
BOLT_HOLE_BEARING = "bolt_hole_bearing"
PLATE_SHEAR_YIELD = "plate_shear_yield"
PLATE_SHEAR_RUPTURE = "plate_shear_rupture"
PLATE_TENSION_YIELD = "plate_tension_yield"
PLATE_TENSION_RUPTURE = "plate_tension_rupture"
PLATE_BLOCK_SHEAR = "plate_block_shear"
FILLET_WELD_SHEAR = "fillet_weld_shear"


@runtime_checkable
class ConnectionRuleCheck(Protocol):
    def check_result(
        self,
        case_name,
        row: Series,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        pass


@runtime_checkable
class ConnectionRuleCheckAndStrengths(ConnectionRuleCheck, Protocol):
    # def check_result(self, case_name, row: Series, design_criteria: DesignType = DesignType.ASD) -> Series:
    #     pass

    def strengths(
        self, case_name: str = None, row: Series = None
    ) -> DesignStrengths:
        pass


@dataclass(frozen=True)
class SimpleShearTabBolted(ConnectionRuleCheckAndStrengths):
    thickness: Quantity
    height: Quantity
    tab_material: IsotropicMaterial
    n_bolts: int
    bolt: AiscBolt
    last_bolt_center_to_height_distance: Quantity
    bolt_center_to_width_distance: Quantity
    thread_in_plane: ThreadCond = ThreadCond.NOT_EXCLUDED
    hole_type: HoleType = HoleType.STANDARD
    connection_type: BearingStrengthType = (
        BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED
    )

    @cached_property
    def _hole_dia(self) -> Quantity:
        return self.bolt.geo.hole_dia(self.hole_type)

    @cached_property
    def _gross_element_area(self):
        return self.height * self.thickness

    @cached_property
    def _net_element_area(self) -> Quantity:
        return (
            self._gross_element_area
            - (self.n_bolts * self._hole_dia) * self.thickness
        )

    @cached_property
    def _bolt_center_spacing(self) -> Quantity:
        if self.bolt == 1:
            return self.height / 2
        return (self.height - 2 * self.last_bolt_center_to_height_distance) / (
            self.n_bolts - 1
        )

    @cached_property
    def _clear_distance_between_holes(self) -> Quantity:
        return self._bolt_center_spacing - self._hole_dia

    @cached_property
    def _clear_distance_to_edge(self) -> Quantity:
        return self.last_bolt_center_to_height_distance - self._hole_dia / 2

    @cached_property
    def _block_shear_net_shear_area(self) -> Quantity:
        return (
            self.height
            - self.last_bolt_center_to_height_distance
            - self._hole_dia * (self.n_bolts - 0.5)
        ) * self.thickness

    @cached_property
    def _block_shear_net_tension_area(self) -> Quantity:
        return (
            self.bolt_center_to_width_distance - self._hole_dia / 2
        ) * self.thickness

    @cached_property
    def _block_shear_gross_shear_area(self) -> Quantity:
        return (
            self.height - self.last_bolt_center_to_height_distance
        ) * self.thickness

    @cached_property
    def _strengths(self):
        if not self.n_bolts == 1:
            bolt_hole_bearing = BoltHolesBearingStrengthMultiple(
                ultimate_stress=self.tab_material.ultimate_stress,
                bolt_diameter=self.bolt.geo.nominal_dia,
                clear_distance_n_bolts_tuples=(
                    (self._clear_distance_between_holes, self.n_bolts - 1),
                    (self._clear_distance_to_edge, 1),
                ),
                thickness=self.thickness,
                connection_type=self.connection_type,
            )
        else:
            bolt_hole_bearing = BoltHolesBearingStrengthMultiple(
                ultimate_stress=self.tab_material.ultimate_stress,
                bolt_diameter=self.bolt.geo.nominal_dia,
                clear_distance_n_bolts_tuples=(
                    (self._clear_distance_to_edge, 1),
                ),
                thickness=self.thickness,
                connection_type=self.connection_type,
            )

        return DesignStrengths(
            strengths={
                BOLT_SHEAR: BoltStrength(
                    nominal_stress=self.bolt.group.nominal_shear_strength(
                        self.thread_in_plane
                    ),
                    nominal_body_area=self.bolt.geo.area,
                    n_bolts=self.n_bolts,
                ),
                BOLT_HOLE_BEARING: bolt_hole_bearing,
                PLATE_SHEAR_YIELD: ShearYield(
                    gross_shear_area=self._gross_element_area,
                    yield_stress=self.tab_material.yield_stress,
                ),
                PLATE_SHEAR_RUPTURE: ShearRupture(
                    net_shear_area=self._net_element_area,
                    ultimate_stress=self.tab_material.ultimate_stress,
                ),
                PLATE_BLOCK_SHEAR: BlockShearStrength(
                    yield_stress=self.tab_material.yield_stress,
                    ultimate_stress=self.tab_material.ultimate_stress,
                    net_shear_area=self._block_shear_net_shear_area,
                    net_tension_area=self._net_element_area,
                    gross_shear_area=self._block_shear_gross_shear_area,
                    tension_distribution_factor=TensionDistribution.UNIFORM,
                ),
            },
            unit=kN,
        )

    def strengths(
        self, case_name: str = None, row: Series = None
    ) -> DesignStrengths:
        return self._strengths

    @cached_property
    def _design_strengths(self):
        return self._strengths.design_strengths

    def design_strength(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType,
    ) -> Quantity:
        return self._strengths.design_strength(design_criteria)

    def check_result(
        self, case_name, row, design_criteria: DesignType = DesignType.ASD
    ) -> Series:
        identifier = f"{SZ}_{case_name}"
        shear_criteria = (
            row[identifier]
            / convert_to(
                self._strengths.design_strength(design_criteria), N
            ).args[0]
        )
        return Series(data={f"criteria_{identifier}": abs(shear_criteria)})


@dataclass(frozen=True)
class WeldShear(ConnectionRuleCheckAndStrengths):
    filler_metal: WeldFillerMaterial
    weld_length: Quantity
    weld_size: Quantity
    theta: Quantity

    @cached_property
    def _strengths(self):
        return DesignStrengths(
            {
                FILLET_WELD_SHEAR: FilletWeld(
                    filler_metal_strength=self.filler_metal.nominal_stress,
                    weld_length=self.weld_length,
                    weld_size=self.weld_size,
                    theta=self.theta,
                ),
            },
            unit=kN,
        )

    def check_result(
        self,
        case_name,
        row: Series,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        identifier = f"{SZ}_{case_name}"
        shear_criteria = (
            row[identifier]
            / convert_to(
                self._strengths.design_strength(design_criteria), N
            ).args[0]
        )
        return Series(data={f"criteria_{identifier}": abs(shear_criteria)})

    def strengths(
        self, case_name: str = None, row: Series = None
    ) -> DesignStrengths:
        return self._strengths


class CompositionsCombination(ABC):
    @abstractmethod
    def compositions(
        self, row: Series = None, case_name: str = None
    ) -> tuple[ConnectionRuleCheckAndStrengths, ...]:
        pass

    @abstractmethod
    def check_result(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> DataFrame:
        pass

    def strengths(
        self, row: Series = None, case_name: str = None
    ) -> DesignStrengths:
        d = dict()
        for composition in self.compositions(row, case_name):
            d.update(**composition.strengths(case_name, row).strengths)
        return DesignStrengths(strengths=d, unit=kN)


@dataclass(frozen=True)
class SimpleShearTabBoltedAndWelded(CompositionsCombination):
    weld_material: WeldFillerMaterial
    weld_length: Quantity
    weld_size: Quantity
    thickness: Quantity
    height: Quantity
    tab_material: IsotropicMaterial
    n_bolts: int
    bolt: AiscBolt
    last_bolt_center_to_height_distance: Quantity
    bolt_center_to_width_distance: Quantity
    thread_in_plane: ThreadCond = ThreadCond.NOT_EXCLUDED
    hole_type: HoleType = HoleType.STANDARD
    connection_type: BearingStrengthType = (
        BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED
    )

    def compositions(
        self, row: Series = None, case_name: str = None
    ) -> tuple[ConnectionRuleCheckAndStrengths, ...]:
        return (
            SimpleShearTabBolted(
                thickness=self.thickness,
                height=self.height,
                tab_material=self.tab_material,
                n_bolts=self.n_bolts,
                bolt=self.bolt,
                last_bolt_center_to_height_distance=self.last_bolt_center_to_height_distance,
                bolt_center_to_width_distance=self.bolt_center_to_width_distance,
                thread_in_plane=self.thread_in_plane,
                hole_type=self.hole_type,
                connection_type=self.connection_type,
            ),
            WeldShear(
                filler_metal=self.weld_material,
                weld_length=self.weld_length,
                weld_size=self.weld_size,
                theta=0 * degree,
            ),
        )

    def check_result(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        identifier = f"{SZ}_{case_name}"
        shear_z = row[f"{SZ}_{case_name}"]
        shear_y = row[f"{SY}_{case_name}"]
        shear = (shear_z**2 + shear_y**2) ** 0.5
        shear_criteria = (
            shear
            / convert_to(
                self.strengths(row, case_name).design_strength(
                    design_criteria
                ),
                N,
            ).args[0]
        )
        return Series(data={f"criteria_{identifier}": abs(shear_criteria)})


def _default_tension_tab(
    tension_tab: "TensionTab",
    row: Series,
    case_name: str,
    design_criteria: DesignType = DesignType.ASD,
) -> Series:
    identifier = f"{FX}_{case_name}"
    shear_criteria = (
        row[identifier]
        / convert_to(
            tension_tab.strengths(
                case_name=case_name, row=row
            ).design_strength(design_criteria),
            N,
        ).args[0]
    )
    return Series(data={f"criteria_{identifier}": abs(shear_criteria)})


class beam_load_conversion(Protocol):
    def __call__(
        self,
        tension_tab: "TensionTab",
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        pass


def bending_moment_conversion(
    tension_tab: "TensionTab",
    row: Series,
    case_name: str,
    design_criteria: DesignType = DesignType.ASD,
) -> Series:
    identifier = f"{MY}_{case_name}"
    tension_at_each_tab = row[identifier] / tension_tab
    shear_criteria = (
        row[identifier]
        / convert_to(
            tension_tab.strengths(
                case_name=case_name, row=row
            ).design_strength(design_criteria),
            N,
        ).args[0]
    )
    return Series(data={f"criteria_{identifier}": abs(shear_criteria)})


@dataclass(frozen=True)
class TensionTab:
    tab_thickness: Quantity
    tab_width: Quantity
    tab_material: IsotropicMaterial
    bolt: AiscBolt
    n_bolts_per_row: int
    distance_first_hole_center_to_edge: Quantity
    distance_between_bolt_center_in_row: Quantity | None = None
    n_bolts_row: int = 1
    thread_in_plane: ThreadCond = ThreadCond.NOT_EXCLUDED
    hole_type: HoleType = HoleType.STANDARD
    connection_type: BearingStrengthType = (
        BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_NOT_ALLOWED
    )
    weld_size: Quantity = None
    weld_length: Quantity = None
    filler_material: WeldFillerMaterial = EXX_70_KSI
    theta: Quantity = 0 * degree
    # load_conversion_function: beam_load_conversion = _default_tension_tab

    def __post_init__(self):
        if (
            self.n_bolts_per_row > 1
            and not self.distance_between_bolt_center_in_row
        ):
            raise ValueError(
                "If n_bolts_per_row > 1 must provide distance_between_bolt_center_in_row"
            )

    @cached_property
    def _clear_distance_between_holes(self) -> Quantity:
        return (
            self.distance_between_bolt_center_in_row
            - self.bolt.geo.hole_dia(hole_type=self.hole_type)
        )

    @cached_property
    def _clear_distance_to_edge(self) -> Quantity:
        return (
            self.distance_first_hole_center_to_edge
            - self.bolt.geo.hole_dia(hole_type=self.hole_type) / 2.0
        )

    @cached_property
    def _strengths(self):
        if not self.n_bolts_per_row == 1:
            bolt_hole_bearing = BoltHolesBearingStrengthMultiple(
                ultimate_stress=self.tab_material.ultimate_stress,
                bolt_diameter=self.bolt.geo.nominal_dia,
                clear_distance_n_bolts_tuples=(
                    (
                        self._clear_distance_between_holes,
                        self.n_bolts_per_row - 1,
                    ),
                    (self._clear_distance_to_edge, 1),
                ),
                thickness=self.tab_thickness,
                connection_type=self.connection_type,
            )
        else:
            bolt_hole_bearing = BoltHolesBearingStrengthMultiple(
                ultimate_stress=self.tab_material.ultimate_stress,
                bolt_diameter=self.bolt.geo.nominal_dia,
                clear_distance_n_bolts_tuples=(
                    (self._clear_distance_to_edge, 1),
                ),
                thickness=self.tab_thickness,
                connection_type=self.connection_type,
            )
        str = {
            BOLT_SHEAR: BoltStrength(
                nominal_stress=self.bolt.group.nominal_shear_strength(
                    thread_condition=self.thread_in_plane
                ),
                n_bolts=self.n_bolts_per_row,
                nominal_body_area=self.bolt.geo.area,
            ),
            BOLT_HOLE_BEARING: bolt_hole_bearing,
            PLATE_TENSION_YIELD: TensileYield(
                yield_stress=self.tab_material.yield_stress,
                gross_area=self.tab_width * self.tab_thickness,
            ),
            PLATE_TENSION_RUPTURE: TensileRupture(
                ultimate_stress=self.tab_material.ultimate_stress,
                net_area=(
                    self.tab_width
                    - self.bolt.geo.hole_dia(self.hole_type) * self.n_bolts_row
                )
                * self.tab_thickness,
            ),
        }
        if self.weld_size:
            str.update(
                **{
                    FILLET_WELD_SHEAR: FilletWeld(
                        weld_size=self.weld_size,
                        weld_length=self.weld_length,
                        filler_metal_strength=self.filler_material.nominal_stress,
                        theta=self.theta,
                    )
                }
            )
        return DesignStrengths(strengths=str, unit=kN)

    def strengths(
        self, case_name: str = None, row: Series = None
    ) -> DesignStrengths:
        return self._strengths

    def check_result(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        identifier = f"{FX}_{case_name}"
        tension_criteria = (
            row[identifier]
            / convert_to(
                self.strengths(case_name=case_name, row=row).design_strength(
                    design_criteria
                ),
                N,
            ).args[0]
        )
        return Series(data={f"criteria_{identifier}": abs(tension_criteria)})

    # def check_result(self, row: Series, case_name: str, design_criteria: DesignType = DesignType.ASD) -> Series:
    #     return self.load_conversion_function(
    #         tension_tab=self,
    #         row=row,
    #         case_name=case_name,
    #         design_criteria=design_criteria
    #     )


@dataclass(frozen=True)
class TensionTabMomentConnection_:
    dist_between_tabs: Quantity


@dataclass(frozen=True)
class TensionTabMomentConnection(TensionTab, TensionTabMomentConnection_):
    def check_result(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        dist_between_tabs = convert_to(self.dist_between_tabs, mm).args[0]
        str = convert_to(
            self.strengths(case_name=case_name, row=row).design_strength(
                design_criteria
            ),
            N,
        ).args[0]
        moment_tension_load = (
            abs(row[f"{MY}_{case_name}"] / dist_between_tabs) / str
        )
        axial_load = abs(row[f"{FX}_{case_name}"] / 2.0) / str
        criteria = moment_tension_load + axial_load
        return Series(
            {
                f"criteria_tension_tab_{MY}_{case_name}": moment_tension_load,
                f"criteria_tension_tab_{FX}_{case_name}": axial_load,
                f"criteria_tension_tab_{case_name}": criteria,
            }
        )


def _moment_to_force(
    dim_hole: Quantity, dim_col: Quantity, moment: Quantity
) -> Quantity:
    return moment / ((dim_col + dim_hole) / 2)


_sum_my = (
    force1 * (dim_z_col + dim_z_hol) / 2.0
    + force2 * (dim_z_hol - dim_z_col)
    + (moment_y + column_axial_load * dim_z_col / 2.0)
)

_sum_mz = (
    force1 * (dim_y_col + dim_y_hol) / 2.0
    + force2 * (dim_y_hol + dim_y_col)
    + (moment_z + column_axial_load * dim_y_col / 2.0)
)

_f = solve([_sum_mz, _sum_my], [force1, force2], dict=True)[0]
_f1, _f2 = _f[force1], _f[force2]


@dataclass
class BasePlateBolts:
    dim_y_hole: Quantity
    dim_z_hole: Quantity
    dim_y_col: Quantity
    dim_z_col: Quantity
    bolt: AiscBolt
    thread_in_plane: ThreadCond = ThreadCond.NOT_EXCLUDED

    def check_result(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        tension_moment_z = (
            _moment_to_force(
                dim_hole=self.dim_y_hole,
                dim_col=self.dim_y_col,
                moment=row[f"{MZ}_{case_name}"] * N * mm,
            ).args[0]
            / 2.0
        )
        tension_moment_y = (
            _moment_to_force(
                dim_hole=self.dim_z_hole,
                dim_col=self.dim_z_col,
                moment=row[f"{MY}_{case_name}"] * N * mm,
            ).args[0]
            / 2.0
        )
        # f1 = _f1.evalf(
        #     subs={
        #         moment_y: row[f"{MY}_{case_name}"],
        #         moment_z: row[f"{MZ}_{case_name}"],
        #         column_axial_load: row[f"{FX}_{case_name}"],
        #         dim_y_col: convert_to(self.dim_y_col, mm).args[0],
        #         dim_z_col: convert_to(self.dim_z_col, mm).args[0],
        #         dim_y_hol: convert_to(self.dim_y_hole, mm).args[0],
        #         dim_z_hol: convert_to(self.dim_z_hole, mm).args[0],
        #     }
        # )
        # f2 = _f2.evalf(
        #     subs={
        #         moment_y: row[f"{MY}_{case_name}"],
        #         moment_z: row[f"{MZ}_{case_name}"],
        #         column_axial_load: row[f"{FX}_{case_name}"],
        #         dim_y_col: convert_to(self.dim_y_col, mm).args[0],
        #         dim_z_col: convert_to(self.dim_z_col, mm).args[0],
        #         dim_y_hol: convert_to(self.dim_y_hole, mm).args[0],
        #         dim_z_hol: convert_to(self.dim_z_hole, mm).args[0],
        #     }
        # )

        axial_tension = row[f"{FX}_{case_name}"] / 8.0
        tension = abs(tension_moment_y) + abs(
            tension_moment_z
        )  # + axial_tension
        tension = max(tension, 0)
        tension = tension * N
        shear_y = row[f"{SY}_{case_name}"] * N
        shear_z = row[f"{SZ}_{case_name}"] * N
        shear: Quantity = (shear_z**2 + shear_y**2) ** 0.5 / 4
        bolt_tension_and_shear_analysis = BoltCombinedTensionAndShear(
            nominal_body_area=self.bolt.geo.area,
            nominal_tensile_stress=self.bolt.group.nominal_tensile_strength,
            nominal_shear_stress=self.bolt.group.nominal_shear_strength(
                thread_condition=self.thread_in_plane
            ),
        )
        bolt_tension_and_shear = bolt_tension_and_shear_analysis.rule_check(
            required_shear_strength_=shear,
            required_tensile_strength_=tension,
            design_criteria=design_criteria,
        ).rename(
            index={
                BOLT_TENSILE_STRENGTH: f"criteria_{BOLT_TENSILE_STRENGTH}_{case_name}",
                BOLT_SHEAR_STRENGTH: f"criteria_{BOLT_SHEAR_STRENGTH}_{case_name}",
            },
        )
        return bolt_tension_and_shear

    # def strengths(self, case_name: str = None, row: Series = None) -> DesignStrengths:
    #     tension_moment_z = _moment_to_force(dim_hole=self.dim_y_hole, dim_col=self.dim_y_col,
    #                                         moment=row[f"{MZ}_{case_name}"])
    #     tension_moment_y = _moment_to_force(dim_hole=self.dim_z_hole, dim_col=self.dim_z_col,
    #                                         moment=row[f"{MY}_{case_name}"])
    #     tension = tension_moment_y + tension_moment_z
    #     shear_y = row[f"{SY}_{case_name}"]
    #     shear_z = row[f"{SZ}_{case_name}"]
    #     shear = sqrt(shear_z ** 2 + shear_y ** 2) / 4
    #     bolt_tension_and_shear = BoltCombinedTensionAndShear(
    #         nominal_body_area=self.bolt.geo.area,
    #         nominal_tensile_stress=self.bolt.group.nominal_tensile_strength,
    #         nominal_shear_stress=self.bolt.group.nominal_shear_strength(thread_condition=self.thread_in_plane),
    #     )
    #     return DesignStrengths()


class WeldSide(int, Enum):
    SINGLE = 1
    DOUBLE = 2


@dataclass(frozen=True)
class BasePlateWeld:


    i_section: AISC_Section
    flanges_type: WeldSide = WeldSide.DOUBLE
    flanges_size: Quantity = 6 * mm
    web_type: WeldSide = WeldSide.DOUBLE
    web_size: Quantity = 6 * mm
    weld_material: WeldFillerMaterial = EXX_70_KSI

    @cached_property
    def _depth(self) -> Quantity:
        return self.i_section.d.rescale("mm").magnitude.item() * mm

    @cached_property
    def _width(self) -> Quantity:
        return self.i_section.bf.rescale("mm").magnitude.item() * mm

    @cached_property
    def _flange_weld_throat(self) -> Quantity:
        return convert_to(self.flanges_size, mm) * 2.0**0.5 / 2.0

    @cached_property
    def _flange_area(self) -> Quantity:
        return self._width * self._flange_weld_throat * self.flanges_type

    @cached_property
    def _web_throat(self):
        return convert_to(self.web_size, mm) * 2.0**0.5 / 2.0

    @cached_property
    def _web_area(self) -> Quantity:
        return self._web_throat * self._depth * self.web_type

    @cached_property
    def _web_weld_throat(self) -> Quantity:
        return convert_to(self.web_size, mm) * 2.0**0.5 / 2.0

    @cached_property
    def _flanges_y_inertia(self):
        return self._flange_area * (self._depth / 2.0) ** 2 * 2

    @cached_property
    def _flanges_z_inertia(self):
        return self._flange_weld_throat * self._width**3 / 12

    @cached_property
    def _inertia_y(self) -> Quantity:
        return self._flanges_y_inertia

    @cached_property
    def _inertia_z(self) -> Quantity:
        return self._flanges_z_inertia

    @cached_property
    def _area(self) -> Quantity:
        return self._flange_area * 2 + self._web_area

    @cached_property
    def _weld_strength(self) -> DesignStrengthMixin:
        return FilletWeldDirectStress(
            filler_metal_strength=self.weld_material.nominal_stress
        )

    def check_result(
        self,
        row: Series,
        case_name: str,
        design_criteria: DesignType = DesignType.ASD,
    ) -> Series:
        """Assumes AISC convention y major and z minor axis (Iy>Iz usually) for shear and moment loads"""

        shear_y = row[f"{SY}_{case_name}"]
        shear_z = row[f"{SZ}_{case_name}"]
        shear = (shear_z**2 + shear_y**2) ** 0.5 / self._area.args[0]
        tension_moment_y = (
            row[f"{MY}_{case_name}"]
            * (self._depth.args[0] / 2.0)
            / self._inertia_y.args[0]
        )
        tension_moment_z = (
            row[f"{MZ}_{case_name}"]
            * (self._width.args[0] / 2.0)
            / self._inertia_z.args[0]
        )
        tension_moment = abs(tension_moment_z) + abs(tension_moment_y)
        # tension = (
        #     row[f"{FX}_{case_name}"] / self._area.args[0] + tension_moment
        # )
        tension = tension_moment
        tension = max(tension, 0)
        stress = (tension**2 + shear**2) ** 0.5
        strength = convert_to(
            self._weld_strength.design_strength(
                design_criteria=design_criteria
            ),
            MPa,
        ).args[0]
        criteria = stress / strength
        return Series(
            data={
                f"criteria_{WELD_STRENGTH}_{case_name}": criteria,
            }
        )
