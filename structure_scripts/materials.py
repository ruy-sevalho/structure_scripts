from dataclasses import dataclass
from functools import cached_property
from typing import Protocol, TYPE_CHECKING

from pylatex import Section
from quantities import Quantity, GPa, MPa, ksi

from structure_scripts.aisc.helpers import _member_slenderness_limit
from structure_scripts.shared.latex_helpers import (
    save_single_entry,
    _dataframe_table_columns,
    _process_quantity_entry_config,
)
from structure_scripts.shared.data import extract_input_dataframe
from structure_scripts.shared.report_config import config_dict


class IsotropicMaterial(Protocol):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity

    def table(self, filter_names: list[str] = None):
        return extract_input_dataframe(
            obj=self,
            extraction_type=IsotropicMaterial,
            filter_names=filter_names,
        )

    @cached_property
    def data_table_df(self):
        return self.table(filter_names=["poisson_ratio"])

    @cached_property
    def latex(self):
        return MaterialLatex(self)


@dataclass
class IsotropicIsotropicMaterialUserDefined(IsotropicMaterial):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity
    density: Quantity | None = None


@dataclass
class MaterialLatex:
    material: "IsotropicMaterial"

    def resume(self):
        save_single_entry(content=self.data_table, file_name="shared.tex")

    @cached_property
    def resume_latex(self):
        return Section(title="Material", data=self.data_table_latex)

    @cached_property
    def data_table_latex(self):
        return _dataframe_table_columns(
            df=self.material.data_table_df,
            unit_display="cell",
            include_description=True,
        )

    @cached_property
    def data_table(self):
        return _dataframe_table_columns(
            df=self.material.data_table_df,
            unit_display="cell",
            include_description=True,
        ).dumps()

    @cached_property
    def modulus_linear(self):
        return _process_quantity_entry_config(
            entry=self.material.modulus_linear,
            print_config=config_dict.modulus_linear,
        )

    @cached_property
    def modulus_shear(self):
        return _process_quantity_entry_config(
            entry=self.material.modulus_shear,
            print_config=config_dict.modulus_shear,
        )

    @cached_property
    def yield_stress(self):
        return _process_quantity_entry_config(
            entry=self.material.yield_stress,
            print_config=config_dict.yield_stress,
        )


# Commonly used materials
steel355MPa = IsotropicIsotropicMaterialUserDefined(
    modulus_linear=200 * GPa,
    modulus_shear=77 * GPa,
    poisson_ratio=0.3,
    yield_stress=355 * MPa,
)

steel250MPa = IsotropicIsotropicMaterialUserDefined(
    modulus_linear=200 * GPa,
    modulus_shear=77 * GPa,
    poisson_ratio=0.3,
    yield_stress=250 * MPa,
)

steel50ksi = IsotropicIsotropicMaterialUserDefined(
    modulus_linear=200 * GPa,
    modulus_shear=77 * GPa,
    poisson_ratio=0.3,
    yield_stress=50 * ksi,
)
