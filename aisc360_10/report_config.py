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
    poisson_ratio: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\nu$"),
        description=NoEscape(r"Poisson"),
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
        description=NoEscape(r"Tens\ão de escoamento"),
        print_units="MPa"
    )
    flange_thickness: PrintOptions = PrintOptions(
        print_units="mm", round_precision=2, label=NoEscape(r"$t_f$"), description="Espessura do flange"
    )
    flange_width: PrintOptions = PrintOptions(
        print_units="mm", round_precision=0, label=NoEscape(r"$b_f$"), description="Largura do flange"
    )
    slender_limit_ratio: PrintOptions = PrintOptions(
        round_precision=2,
        label=NoEscape(r"$\alpha_p$"),
        description=NoEscape(r"Limite de esbeltez esbelto/(n\~ao esbelto ou n\~ao compacto)")
    )
    compact_limit_ratio: PrintOptions = PrintOptions(
        round_precision=2, label=NoEscape(r"$\alpha_r$"), description=NoEscape(
            r"Limite de esbeltez compacto/n\~ao compacto"
        )
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
    coefficient_c: PrintOptions = PrintOptions(
        round_precision=1,
        label=NoEscape(r"$c$"),
        description=NoEscape(r"Coeficiente $c$")
    )
    mod_factor: PrintOptions = PrintOptions(
        round_precision=1,
        label=NoEscape(r"$C_b$"),
        description=NoEscape(r"Coeficiente de modifica\c{c}\~ao de flambagem lateral torsional")
    )
    area: PrintOptions = PrintOptions(
        print_units="cm ** 2",
        round_precision=2,
        label=NoEscape(r"$A_g$"),
        description=NoEscape(r"\'Area bruta da se\c{c}\~ao transversal")
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
    effective_radius_of_gyration: PrintOptions = PrintOptions(
        print_units="cm",
        round_precision=2,
        label=NoEscape(r"$r_{ts}$"),
        description=NoEscape(r"Raio de gira\c{c}\~ao efetivo")
    )
    torsional_constant: PrintOptions = PrintOptions(
        print_units="cm ** 4",
        round_precision=2,
        label=NoEscape(r"$J$"),
        description=NoEscape(r"Momento Polar de In\'ercia")
    )
    torsional_radius_of_gyration: PrintOptions = PrintOptions(
        print_units="cm",
        round_precision=2,
        label=NoEscape(r"$r_z$"),
        description=NoEscape(r"Raio de gira\c{c}\~ao torsional")
    )
    warping_constant: PrintOptions = PrintOptions(
        print_units="cm ** 6",
        round_precision=2,
        label=NoEscape(r"$C_w$"),
        description=NoEscape(r"Constante de \emph{warping}")
    )
    construction: PrintOptions = PrintOptions(
        label="-",
        description=NoEscape(r"Tipo de constru\c{c}\~ao")
    )
    factor_k: PrintOptions = PrintOptions(
        label=NoEscape(r"$k$"),
        round_precision=1,
        description="Fator de comprimento efetivo (flambagem)"
    )
    unbraced_length: PrintOptions = PrintOptions(
        label=NoEscape(r"$L$"),
        round_precision=0,
        print_units="mm",
        description="Comprimento entre suportes da viga"
    )
    minor_axis_slenderness: PrintOptions = PrintOptions(
        round_precision=2
    )
    slenderness_limit = PrintOptions(round_precision=2)
    elastic_buckling_critical_stress: PrintOptions = PrintOptions(
        label=NoEscape(r"F_e"),
        round_precision=2,
        print_units="MPa",
        description=NoEscape(r"Tens\~ao cr\'itica de flambagem elástica")
    )
    critical_stress: PrintOptions = PrintOptions(
        label=NoEscape(r"F_{cr}"),
        round_precision=2,
        print_units="MPa",
        description=NoEscape(r"Tens\~ao cr\'itica")
    )
    strength_force: PrintOptions = PrintOptions(
        label=NoEscape(r"P_{n}"),
        round_precision=2,
        print_units="kN",
        description=NoEscape(r"Carga cr\'itica nomimal")
    )
    strength_moment: PrintOptions = PrintOptions(
        label=NoEscape(r"M_{n}"),
        round_precision=2,
        print_units="kN*m",
        description=NoEscape(r"Momento cr\'itica nomimal")
    )
    limit_length_flexural_yield: PrintOptions = PrintOptions(
        label=NoEscape(r"L_p"),
        round_precision=0,
        description="Comprimento limite em flexão para o caso de escoamento ",
        print_units="mm"
    )
    limit_length_flexural_lateral_torsional_buckling: PrintOptions = PrintOptions(
        label=NoEscape(r"L_r"),
        round_precision=0,
        description="Comprimento limite em flexão para o caso de flambagem lateral tosrional.",
        print_units="mm"
    )

    def to_dict(self):
        return {field_.name: getattr(self, field_.name) for field_ in fields(self)}
