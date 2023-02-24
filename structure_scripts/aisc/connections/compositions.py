from dataclasses import dataclass
from functools import cached_property

from pandas import DataFrame
from sympy.physics.units import Quantity

from structure_scripts.aisc.connections.bolt_criteria import BoltStrength
from structure_scripts.aisc.connections.bolts import AiscBolt, ThreadCond, HoleType
from structure_scripts.aisc.connections.elements import ShearYield, ShearRupture, BoltHolesBearingStrength, \
    BoltHolesBearingStrengthMultiple, BearingStrengthType, BlockShearStrength, TensionDistribution
from structure_scripts.aisc.connections.materials import (
    IsotropicMaterial,
    WeldFillerMaterial,
)
from structure_scripts.aisc.criteria import DesignType, DesignStrengths
from structure_scripts.units.sympy_units import kN

BOLT_SHEAR = "bolt_shear"
BOLT_HOLE_BEARING = "bolt_hole_bearing"
PLATE_SHEAR_YIELD = "plate_shear_yield"
PLATE_SHEAR_RUPTURE = "plate_shear_rupture"
PLATE_TENSION_YIELD = "plate_tension_yield"
PLATE_TENSION_RUPTURE = "plate_tension_rupture"
PLATE_BLOCK_SHEAR = "plate_block_shear"


@dataclass(frozen=True)
class SimpleShearTabBolted:
    thickness: Quantity
    height: Quantity
    tab_material: IsotropicMaterial
    n_bolts: int
    bolt: AiscBolt
    last_bolt_center_to_height_distance: Quantity
    bolt_center_to_width_distance: Quantity
    thread_in_plane: ThreadCond = ThreadCond.NOT_EXCLUDED
    hole_type: HoleType = HoleType.STANDARD
    connection_type: BearingStrengthType = BearingStrengthType.DEFORMATION_AT_SERVICE_LOAD_ALLOWED

    @cached_property
    def _hole_dia(self) -> Quantity:
        return self.bolt.geo.hole_dia(self.hole_type)

    @cached_property
    def _gross_element_area(self):
        return self.height * self.thickness

    @cached_property
    def _net_element_area(self) -> Quantity:
        return self._gross_element_area - (self.n_bolts * self._hole_dia) * self.thickness

    @cached_property
    def _bolt_center_spacing(self) -> Quantity:
        return (self.height - 2 * self.last_bolt_center_to_height_distance) / (self.n_bolts - 1)

    @cached_property
    def _clear_distance_between_holes(self) -> Quantity:
        return self._bolt_center_spacing - self._hole_dia

    @cached_property
    def _clear_distance_to_edge(self) -> Quantity:
        return self.last_bolt_center_to_height_distance - self._hole_dia / 2

    @cached_property
    def _block_shear_net_shear_area(self) -> Quantity:
        return (self.height - self.last_bolt_center_to_height_distance - self._hole_dia * (self.n_bolts - .5)) * self.thickness

    @cached_property
    def _block_shear_net_tension_area(self) -> Quantity:
        return (self.bolt_center_to_width_distance - self._hole_dia / 2) * self.thickness

    @cached_property
    def _block_shear_gross_shear_area(self) -> Quantity:
        return (self.height - self.last_bolt_center_to_height_distance) * self.thickness

    @cached_property
    def strengths(self):
        return DesignStrengths(
            strengths={
                BOLT_SHEAR: BoltStrength(
                    nominal_stress=self.bolt.group.nominal_shear_strength(self.thread_in_plane),
                    nominal_body_area=self.bolt.geo.area,
                    n_bolts=self.n_bolts
                ),
                BOLT_HOLE_BEARING: BoltHolesBearingStrengthMultiple(
                    ultimate_stress=self.tab_material.ultimate_stress,
                    bolt_diameter=self.bolt.geo.nominal_dia,
                    clear_distance_n_bolts_tuples=(
                        (self._clear_distance_between_holes, self.n_bolts -1),
                        (self._clear_distance_to_edge, 1)
                    ),
                    thickness=self.thickness,
                    connection_type=self.connection_type
                ),
                PLATE_SHEAR_YIELD: ShearYield(
                    gross_shear_area=self._gross_element_area,
                    yield_stress=self.tab_material.yield_stress
                ),
                PLATE_SHEAR_RUPTURE: ShearRupture(
                    net_shear_area=self._net_element_area,
                    ultimate_stress=self.tab_material.ultimate_stress
                ),
                PLATE_BLOCK_SHEAR: BlockShearStrength(
                    yield_stress=self.tab_material.yield_stress,
                    ultimate_stress=self.tab_material.ultimate_stress,
                    net_shear_area=self._block_shear_net_shear_area,
                    net_tension_area=self._net_element_area,
                    gross_shear_area=self._block_shear_gross_shear_area,
                    tension_distribution_factor=TensionDistribution.UNIFORM
                )
            },
            unit=kN
        )

    @cached_property
    def design_strengths(self):
        return self.strengths.design_strengths