from dataclasses import dataclass
from functools import cached_property
from typing import Protocol

from pandas import DataFrame, concat
from quantities import Quantity, m

from structure_scripts.api_rpa.elements import CircularSection
from structure_scripts.api_rpa.helpers import _c_coefficient_collum_buck, _allowable_compressive_stress_a, \
    _allowable_compressive_stress_b, ratio_limit_a, allowable_bending_stress_a, beam_shear_stress, \
    allowable_shear_stress, max_torsional_shear_stress, axial_stress, bending_stress, \
    combined_bending_compression_criteria_a, combined_bending_compression_criteria_b
from structure_scripts.shared.data import extract_input_dataframe
from structure_scripts.shared.helpers import member_slenderness_ratio, same_units_simplify, ratio_simplify


class Analysis(Protocol):
    allowable_stress: Quantity

    def acting_stress(self, load: Quantity) -> Quantity:
        ...

    def criteria_ratio(self, load: Quantity):
        return ratio_simplify(abs(self.acting_stress(load=load)), self.allowable_stress)


@dataclass
class Axial:
    profile: CircularSection

    def acting_stress(self, load: Quantity) -> Quantity:
        return axial_stress(axial_force=load, cross_area=self.profile.geometry.area)


@dataclass
class AxialTension(Axial, Analysis):
    profile: CircularSection

    @cached_property
    def allowable_stress(self):
        return 0.6 * self.profile.material.yield_stress


@dataclass
class AxialCompression(Axial, Analysis):
    profile: CircularSection
    length: Quantity
    factor_k: float = 1.

    @cached_property
    def coefficient_c(self):
        return _c_coefficient_collum_buck(
            yield_stress=self.profile.material.yield_stress,
            modulus_linear=self.profile.material.modulus_linear
        )

    @cached_property
    def slenderness(self):
        return member_slenderness_ratio(
            unbraced_length=self.length,
            factor_k=self.factor_k,
            radius_of_gyration=self.profile.geometry.radius_of_gyration
        )

    @cached_property
    def allowable_stress_a(self):
        return _allowable_compressive_stress_a(
            slenderness=self.slenderness,
            c=self.coefficient_c,
            yield_stress=self.profile.material.yield_stress
        )

    @cached_property
    def allowable_stress_b(self):
        return _allowable_compressive_stress_b(
            slenderness=self.slenderness,
            modulus_linear=self.profile.material.modulus_linear
        )

    @cached_property
    def allowable_stress(self):
        if self.slenderness < self.coefficient_c:
            return self.allowable_stress_a
        return self.allowable_stress_b


@dataclass
class Bending(Analysis):
    profile: CircularSection

    @cached_property
    def dia_thick_ratio_limit_a(self):
        return ratio_limit_a(yield_stress=self.profile.material.yield_stress)

    @cached_property
    def allowable_stress_a(self):
        return allowable_bending_stress_a(yield_stress=self.profile.material.yield_stress)

    @cached_property
    def allowable_stress(self):
        ratio = self.profile.geometry.outer_diameter / self.profile.geometry.wall_thickness
        if ratio < self.dia_thick_ratio_limit_a:
            return self.allowable_stress_a
        raise NotImplementedError

    def acting_stress(self, load: Quantity) -> Quantity:
        return bending_stress(bending_moment=load, section_modulus=self.profile.geometry.section_modulus)


@dataclass
class Shear(Analysis):
    profile: CircularSection

    def acting_stress(self, load: Quantity):
        return beam_shear_stress(shear_force=load, cross_area=self.profile.geometry.area)

    @cached_property
    def allowable_stress(self):
        return allowable_shear_stress(yield_stress=self.profile.material.yield_stress)


@dataclass
class Torsion(Analysis):
    profile: CircularSection

    def acting_stress(self, load: Quantity):
        return max_torsional_shear_stress(
            outer_diameter=self.profile.geometry.outer_diameter,
            torsional_moment=load,
            polar_inertia=self.profile.geometry.polar_moment_of_inertia
        )

    @cached_property
    def allowable_stress(self):
        return allowable_shear_stress(yield_stress=self.profile.material.yield_stress)


@dataclass
class BeamModel:
    profile: CircularSection
    length: Quantity = 1.0 * m
    factor_k: float = 1.0

    @property
    def tension(self):
        return AxialTension(profile=self.profile)

    @cached_property
    def compression(self):
        return AxialCompression(profile=self.profile, length=self.length, factor_k=self.factor_k)

    @cached_property
    def bending(self):
        return Bending(profile=self.profile)

    @cached_property
    def torsion(self):
        return Torsion(profile=self.profile)

    @cached_property
    def shear(self):
        return Shear(profile=self.profile)

    def results(
            self,
            axial_force: Quantity,
            bending_moment_x: Quantity,
            bending_moment_y: Quantity,
            shear_force: Quantity,
            torsion_moment: Quantity,
    ):
        return BeamResult(
            model=self,
            axial_force=axial_force,
            bending_moment_x=bending_moment_x,
            bending_moment_y=bending_moment_y,
            shear_force=shear_force,
            torsion_moment=torsion_moment
        )


@dataclass
class BeamResult:
    model: BeamModel
    axial_force: Quantity
    bending_moment_x: Quantity
    bending_moment_y: Quantity
    shear_force: Quantity
    torsion_moment: Quantity
    modification_coefficient: float = 0.85

    def __post_init__(self):
        self.compression_marker = False
        if self.axial_force < 0:
            self.compression_marker = True

    @cached_property
    def acting_axial_stress(self):
        return self.model.tension.acting_stress(load=abs(self.axial_force))

    @cached_property
    def acting_bending_stress_x(self):
        return self.model.bending.acting_stress(load=self.bending_moment_x)

    @cached_property
    def acting_bending_stress_y(self):
        return self.model.bending.acting_stress(load=self.bending_moment_y)

    @cached_property
    def acting_shear_stress(self):
        return self.model.shear.acting_stress(load=self.shear_force)

    @cached_property
    def acting_torsional_tress(self):
        return self.model.torsion.acting_stress(load=self.torsion_moment)

    @cached_property
    def combined_axial_bending_criteria_a(self):
        return combined_bending_compression_criteria_a(
            acting_compressive_stress=self.acting_axial_stress,
            acting_bending_stress_x=self.acting_bending_stress_x,
            acting_bending_stress_y=self.acting_bending_stress_y,
            elastic_compressive_buckling_stress=self.model.compression.allowable_stress_b,
            allowable_compressive_stress=self.model.compression.allowable_stress,
            allowable_bending_stress=self.model.bending.allowable_stress,
            modification_coefficient=self.modification_coefficient
        ).magnitude

    @cached_property
    def combined_axial_bending_criteria_b(self):
        return combined_bending_compression_criteria_b(
            acting_compressive_stress=self.acting_axial_stress,
            acting_bending_stress_x=self.acting_bending_stress_x,
            acting_bending_stress_y=self.acting_bending_stress_y,
            allowable_bending_stress=self.model.bending.allowable_stress,
            yield_stress=self.model.profile.material.yield_stress
        ).magnitude

    @cached_property
    def combined_tension_bending_criteria(self):
        return self.combined_axial_bending_criteria_b

    @cached_property
    def loads_df(self):
        return extract_input_dataframe(self, filter_names=["model"])

    @cached_property
    def combined_result_df(self):
        if self.compression_marker:
            result_tension = None
            result_comp_a = self.combined_axial_bending_criteria_a
            result_comp_b = self.combined_axial_bending_criteria_b
        else:
            result_tension = self.combined_axial_bending_criteria_b
            result_comp_a = None
            result_comp_b = None
        return DataFrame(
            {
                "tension_bending": [result_tension],
                "compression_bending_a": [result_comp_a],
                "compression_bending_b": [result_comp_b],
            }
        )

    @cached_property
    def simple_results(self):
        return DataFrame(
            {
                "torsion": [self.model.torsion.criteria_ratio(self.torsion_moment)],
                "shear": [self.model.shear.criteria_ratio(self.shear_force)]
            }
        )

    @cached_property
    def results(self):
        return concat(
            (self.loads_df, self.simple_results, self.combined_result_df),
            axis=1
        )

