from dataclasses import dataclass, fields
from typing import Optional
from pylatex import NoEscape


@dataclass
class PrintOptions:
    """[summary]"""

    print_units: Optional[str] = None
    round_precision: int = 2
    label: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ReportConfig:
    name: PrintOptions = PrintOptions()
    modulus_x: PrintOptions = PrintOptions(
        print_units="GPa",
        label=r"E\textsubscript{x}",
        description="Modulus of elasticity - x direction",
    )
    modulus_y: PrintOptions = PrintOptions(print_units="GPa")
    modulus_xy: PrintOptions = PrintOptions(print_units="GPa")
    density: PrintOptions = PrintOptions(round_precision=0)
    max_strain_x: PrintOptions = PrintOptions()
    max_strain_xy: PrintOptions = PrintOptions()
    f_mass_cont: PrintOptions = PrintOptions()
    f_area_density: PrintOptions = PrintOptions()
    thickness: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label="t"
    )
    thickness_outer: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label=NoEscape(r"t\textsubscript{o}")
    )
    thickness_inner: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label=NoEscape(r"t\textsubscript{i}")
    )
    orientation: PrintOptions = PrintOptions()
    multiple: PrintOptions = PrintOptions()
    strength_shear: PrintOptions = PrintOptions()
    modulus_shear: PrintOptions = PrintOptions()
    strength_tens: PrintOptions = PrintOptions()
    modulus_tens: PrintOptions = PrintOptions()
    strength_comp: PrintOptions = PrintOptions()
    modulus_comp: PrintOptions = PrintOptions()
    resin_absorption: PrintOptions = PrintOptions()
    core_type: PrintOptions = PrintOptions()
    dimension_web: PrintOptions = PrintOptions()
    dimension_flange: PrintOptions = PrintOptions()
    linear_strain_ratio: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\epsilon$"),
        description="Linear strain",
    )
    linear_strain_ratio_simp: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\epsilon$\textsubscript{s}"),
        description="Linear strain",
    )
    linear_strain_ratio_bottom: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\epsilon$\textsubscript{B}"),
        description="Linear strain",
    )
    linear_strain_ratio_top: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\epsilon$\textsubscript{T}"),
        description="Linear strain",
    )
    shear_strain_ratio: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\gamma$"),
        description="Shear strain",
    )
    shear_strain_buckling_ratio: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\gamma$\textsubscript{buck}"),
        description="Buckling shear strain",
    )
    design_pressure_type: PrintOptions = PrintOptions(
        label=NoEscape(r"{design p\\ type}")
    )
    design_pressure: PrintOptions = PrintOptions(label="design p")
    core_shear_stress_ratio: PrintOptions = PrintOptions(
        label=NoEscape(r"$\gamma$\textsubscript{core}")
    )
    skin_wrinkling_ratio: PrintOptions = PrintOptions(
        label=NoEscape(r"$\epsilon$\textsubscript{wrinkle}")
    )

    def to_dict(self):
        return {field_.name: getattr(self, field_.name) for field_ in fields(self)}


modulus_print_options = PrintOptions(print_units="GPa")
density_print_options = PrintOptions(round_precision=0)
max_strain_print_options = PrintOptions()
f_mass_cont_print_options = PrintOptions(round_precision=0)
f_area_density_print_options = PrintOptions(round_precision=3)
thickness_print_options = PrintOptions(print_units="mm")
orientation_print_options = PrintOptions(round_precision=1)
multiple_print_options = PrintOptions(round_precision=0)
strength_shear_print_options = PrintOptions(round_precision=0)
dimension_web_print_options = PrintOptions(print_units="mm")
dimension_flange_print_options = PrintOptions(print_units="mm")

default_report_config = ReportConfig(
    modulus_x=modulus_print_options,
    modulus_y=modulus_print_options,
    modulus_xy=modulus_print_options,
    density=density_print_options,
    max_strain_x=max_strain_print_options,
    max_strain_xy=max_strain_print_options,
    f_mass_cont=f_mass_cont_print_options,
    f_area_density=f_area_density_print_options,
    thickness=thickness_print_options,
    orientation=orientation_print_options,
    multiple=multiple_print_options,
    strength_shear=strength_shear_print_options,
    modulus_shear=modulus_print_options,
    strength_tens=strength_shear_print_options,
    modulus_tens=modulus_print_options,
    strength_comp=strength_shear_print_options,
    modulus_comp=modulus_print_options,
    resin_absorption=PrintOptions(),
    core_type=PrintOptions(),
    dimension_flange=dimension_flange_print_options,
    dimension_web=dimension_web_print_options,
)
