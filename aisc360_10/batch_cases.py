from functools import partial
from typing import Collection

import pandas as pd
from quantities import Quantity
from aisc360_10.elements import (
    BeamCompressionFlexureDoublySymmetricEffectiveLength,
    DoublySymmetricIUserDefined
)


def several_loads_results(
        profile: DoublySymmetricIUserDefined,
        unbraced_length: Quantity,
        loads: Collection[tuple[Quantity, Quantity, Quantity]],
        factor_k_minor_axis: float = 1.0,
        factor_k_major_axis: float = 1.0,
        factor_k_torsion: float = 1.0,
        names: Collection[str] | None = None

):
    partial_beam = partial(
        BeamCompressionFlexureDoublySymmetricEffectiveLength,
        profile=profile,
        unbraced_length=unbraced_length,
        factor_k_torsion=factor_k_torsion,
        factor_k_major_axis=factor_k_major_axis,
        factor_k_minor_axis=factor_k_minor_axis
    )
    results_df = pd.DataFrame()
    for load in loads:
        beam: BeamCompressionFlexureDoublySymmetricEffectiveLength = partial_beam(
            required_axial_strength=load[0],
            required_major_axis_flexure_strength=load[1],
            required_minor_axis_flexure_strength=load[2],
        )
        results_df = pd.concat((results_df, beam.results_h1_df))
    return results_df
