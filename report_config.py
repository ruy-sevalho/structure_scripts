from dataclasses import dataclass, fields
from typing import Optional
from pylatex import NoEscape, Math


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
    modulus_linear: PrintOptions = PrintOptions(
        round_precision=0,
        print_units="GPa",
        label=NoEscape(r"$E$"),
        description=NoEscape(r"M\'odulo de elasticidade"),
    )
    modulus_shear: PrintOptions = PrintOptions(
        print_units="GPa",
        label=NoEscape(r"$G$"),
        description=NoEscape(r"M\ódulo de elasticidade transversal"),
        round_precision=0,
    )
    density: PrintOptions = PrintOptions(
        round_precision=0,
        label=NoEscape(r"\rho"),
        description="Densidade"
    )
    yield_stress: PrintOptions = PrintOptions(
        round_precision=0,
        label=NoEscape(r"$F_y$"),
        description=NoEscape(r"Tens\ão de escoamento")
    )
    flange_thickness: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label=NoEscape(r"$t_f$"), description="Espessura do flange"
    )
    flange_width: PrintOptions = PrintOptions(
        print_units="mm", round_precision=0, label=NoEscape(r"$b_f$"), description="Largura do flange"
    )
    flange_axial_limit_ratio: PrintOptions = PrintOptions(
        round_precision=2, label=NoEscape(r"$\alpha_r$"), description="Limite esbeltez"
    )
    web_height: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label=NoEscape(r"$w_h$"), description="Altura da alma"
    )
    web_thickness: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label=NoEscape(r"$t_w$"), description="Espessura da alma"
    )
    total_height: PrintOptions = PrintOptions(
        print_units="mm", round_precision=0, label=NoEscape(r"$d$"), description="Altura total do perfil"
    )
    distance_between_centroids: PrintOptions = PrintOptions(
        print_units="mm",
        round_precision=2,
        label=NoEscape(r"$h_0$"),
        description=NoEscape(r"Dist\^ancia entre centro\'ides dos flanges")
    )
    area: PrintOptions = PrintOptions(
        print_units="cm ** 2",
        round_precision=2,
        label=NoEscape(r"$A$"),
        description=NoEscape(r"\'Area da se\c{c}\~ao transversal")
    )
    major_axis_inertia: PrintOptions = PrintOptions(
        print_units="cm ** 4",
        round_precision=2,
        label=NoEscape(r"$I_x$"),
        description=NoEscape(r"Momento de in\'ercia do eixo principal")
    )
    minor_axis_inertia: PrintOptions = PrintOptions(
        print_units="cm ** 4",
        round_precision=2,
        label=NoEscape(r"$I_y$"),
        description=NoEscape(r"Momento de in\'ercia do eixo secund\'ario")
    )
    major_axis_elastic_section_modulus: PrintOptions = PrintOptions(
        print_units="cm ** 3",
        round_precision=2,
        label=NoEscape(r"$S_x$"),
        description=NoEscape(r"Momento de in\'ercia el\'astico do eixo principal")
    )
    major_axis_plastic_section_modulus: PrintOptions = PrintOptions(
        print_units="cm ** 3",
        round_precision=2,
        label=NoEscape(r"$Z_x$"),
        description=NoEscape(r"Momento de in\'ercia do eixo principal")
    )
    major_axis_radius_of_gyration: PrintOptions = PrintOptions(
        print_units="cm",
        round_precision=2,
        label=NoEscape(r"$r_x$"),
        description=NoEscape(r"Raio de gira\c{c}\~ao do eixo principal")
    )
    minor_axis_elastic_section_modulus: PrintOptions = PrintOptions(
        print_units="cm ** 3",
        round_precision=2,
        label=NoEscape(r"$S_y$"),
        description=NoEscape(r"Momento de in\'ercia el\'astico do eixo secund\'ario")
    )
    minor_axis_plastic_section_modulus: PrintOptions = PrintOptions(
        print_units="cm ** 3",
        round_precision=2,
        label=NoEscape(r"$Z_y$"),
        description=NoEscape(r"Momento de in\'ercia do eixo secund\'ario")
    )
    minor_axis_radius_of_gyration: PrintOptions = PrintOptions(
        print_units="cm",
        round_precision=2,
        label=NoEscape(r"$r_y$"),
        description=NoEscape(r"Raio de gira\c{c}\~ao do eixo secund\'ario")
    )
    torsional_constant: PrintOptions = PrintOptions(
        print_units="cm ** 4",
        round_precision=2,
        label=NoEscape(r"$J$"),
        description=NoEscape(r"Momento Polar de In\'ercia")
    )
    construction: PrintOptions = PrintOptions(
        label="-",
        description=NoEscape(r"Tipo de constru\c{c}\~ao")
    )

    def to_dict(self):
        return {field_.name: getattr(self, field_.name) for field_ in fields(self)}
