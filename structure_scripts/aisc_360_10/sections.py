from abc import abstractmethod
from typing import Protocol, TYPE_CHECKING, Union, TypeVar
from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    DesignType,
    StrengthType,
    DesignStrength,
)

# from structure_scripts.aisc_360_10.section_slenderness import (
#     FlangeWebSlenderness,
# )

if TYPE_CHECKING:
    pass
#
#
# class WebArea(Protocol):
#     """Extra area"""
#
#     web_area_major_axis: Quantity
#     web_area_minor_axis: Quantity
#
#
# class WebShearParameters(Protocol):
#     web_shear_coefficient_major_axis: float
#     web_shear_buckling_coefficient_major_axis: float
#     web_shear_coefficient_minor_axis: float
#     web_shear_buckling_coefficient_minor_axis: float
#

# class AreaProperties(Protocol):
#     area: Quantity
#     major_axis_inertia: Quantity
#     major_axis_elastic_section_modulus: Quantity
#     major_axis_plastic_section_modulus: Quantity
#     major_axis_radius_of_gyration: Quantity
#     minor_axis_inertia: Quantity
#     minor_axis_elastic_section_modulus: Quantity
#     minor_axis_plastic_section_modulus: Quantity
#     minor_axis_radius_of_gyration: Quantity
#     torsional_constant: Quantity
#     torsional_radius_of_gyration: Quantity
#     warping_constant: Quantity
#
#     # Don't be mad future me. At least it worked
#     def table(self, filter_names: list[str] = None):
#         return extract_input_dataframe(obj=self, extraction_type=AreaProperties, filter_names=filter_names)
#
#     @cached_property
#     def data_table_df(self):
#         return self.table(filter_names=["torsional_radius_of_gyration", "warping_constant"])
#
#     @cached_property
#     def latex(self):
#         return AreaPropertiesLatex(data.py=self)


# class AreaPropertiesWithWeb(AreaProperties, WebArea):
#     ...

LoadReturn = TypeVar(
    "LoadReturn",
    dict[StrengthType, Quantity],
    dict[
        StrengthType, tuple[Quantity, dict[str, Union[Quantity, float, bool]]]
    ],
)


class AISC_360_10_Rule_Check(Protocol):
    def compression(
        self,
        length_major_axis: Quantity,
        factor_k_major_axis: float = 1.0,
        length_minor_axis: Quantity = None,
        factor_k_minor_axis: float = 1.0,
        length_torsion: Quantity = None,
        factor_k_torsion: float = 1.0,
    ) -> DesignStrength:
        ...

    def flexure_major_axis(
        self,
        length: Quantity,
        lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> DesignStrength:
        ...

    def flexure_minor_axis(
        self,
        length: Quantity,
        # lateral_torsional_buckling_modification_factor: float = 1.0,
        design_type: DesignType = DesignType.ASD,
    ) -> DesignStrength:
        ...

    def shear_major_axis(self) -> DesignStrength:
        ...

    def shear_minor_axis(self) -> DesignStrength:
        ...
