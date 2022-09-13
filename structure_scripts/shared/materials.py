from dataclasses import dataclass
from functools import cached_property
from typing import Protocol, TYPE_CHECKING

from quantities import Quantity

if TYPE_CHECKING:
    from structure_scripts.shared.data import extract_input_dataframe
    from structure_scripts.aisc_360_10.elements_latex import MaterialLatex


class Material(Protocol):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity

    def table(self, filter_names: list[str] = None):
        return extract_input_dataframe(obj=self, extraction_type=Material, filter_names=filter_names)

    @cached_property
    def data_table_df(self):
        return self.table(filter_names=["poisson_ratio"])

    @cached_property
    def latex(self):
        return MaterialLatex(self)


@dataclass
class IsoTropicMaterial(Material):
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity
    density: Quantity | None = None


