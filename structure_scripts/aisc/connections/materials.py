from dataclasses import dataclass

from sympy.physics.units import Quantity, kg, m, convert_to

from structure_scripts.units.sympy_units import MPa


@dataclass(frozen=True)
class IsotropicMaterial:
    modulus_linear: Quantity
    modulus_shear: Quantity
    poisson_ratio: float
    yield_stress: Quantity
    ultimate_stress: Quantity
    density: Quantity | None = None

    @classmethod
    def new(
        cls,
        modulus_linear: Quantity,
        modulus_shear: Quantity,
        poisson_ratio: float,
        yield_stress: Quantity,
        ultimate_stress: Quantity | None = None,
        density: Quantity | None = None,
    ) -> "IsotropicMaterial":
        return cls(
            modulus_linear=modulus_linear,
            modulus_shear=modulus_shear,
            poisson_ratio=poisson_ratio,
            yield_stress=yield_stress,
            ultimate_stress=ultimate_stress or yield_stress,
            density=density,
        )


@dataclass(frozen=True)
class WeldFillerMaterial:
    nominal_stress: Quantity


ASTM_A_36 = IsotropicMaterial(
    modulus_linear=200000.0 * MPa,
    modulus_shear=79300.0 * MPa,
    poisson_ratio=0.26,
    yield_stress=250.0 * MPa,
    ultimate_stress=400.0 * MPa,
    density=7800.0 * kg / m**3,
)
EXX_60_KSI = WeldFillerMaterial(nominal_stress=413.685 * MPa)
EXX_70_KSI = WeldFillerMaterial(nominal_stress=485. * MPa)