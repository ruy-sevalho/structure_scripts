from abc import abstractmethod
from typing import Protocol, TYPE_CHECKING, Union, TypeVar
from quantities import Quantity

from structure_scripts.aisc_360_10.criteria import (
    DesignType,
    StrengthType,
    DesignStrength,
)
from structure_scripts.section import Profile

LoadReturn = TypeVar(
    "LoadReturn",
    dict[StrengthType, Quantity],
    dict[
        StrengthType, tuple[Quantity, dict[str, Union[Quantity, float, bool]]]
    ],
)


class AISC_360_10_Rule_Check(Profile, Protocol):
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
    ) -> DesignStrength:
        ...

    def flexure_minor_axis(
        self,
        # length: Quantity,
        # lateral_torsional_buckling_modification_factor: float = 1.0,
    ) -> DesignStrength:
        ...

    def shear_major_axis(self) -> DesignStrength:
        ...

    def shear_minor_axis(self) -> DesignStrength:
        ...

    # def load_check(
    #     self,
    # ):
    #     return
