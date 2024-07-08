from dataclasses import dataclass, field, fields
from functools import partial
from typing import Optional
from enum import Enum
from pylatex import NoEscape


class Language(Enum):
    ENGLISH = "ENGLISH"
    PORTUGUESE = "PORTUGUESE"


@dataclass
class PrintOptions:
    """[summary]"""

    print_units: Optional[str] = None
    round_precision: int = 2
    label: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ReportConfig:
    name: PrintOptions = field(default_factory=PrintOptions)
    modulus_linear: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=0,
            print_units="GPa",
            label=NoEscape(r"$E$"),
            description=NoEscape(r"M\'odulo de elasticidade"),
        )
    )
    poisson_ratio: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=2,
            label=NoEscape(r"$\nu$"),
            description=NoEscape(r"Poisson"),
        )
    )
    modulus_shear: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="GPa",
            label=NoEscape(r"$G$"),
            description=NoEscape(r"M\'odulo de elasticidade transversal"),
            round_precision=0,
        )
    )
    density: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=0,
            label=NoEscape(r"\rho"),
            description="Densidade",
        )
    )
    yield_stress: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=0,
            label=NoEscape(r"$F_y$"),
            description=NoEscape(r"Tens\~ao de escoamento"),
            print_units="MPa",
        )
    )
    flange_thickness: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="mm",
            round_precision=2,
            label=NoEscape(r"$t_f$"),
            description="Espessura do flange",
        )
    )
    flange_width: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="mm",
            round_precision=0,
            label=NoEscape(r"$b_f$"),
            description="Largura do flange",
        )
    )
    flange_slenderness: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=2,
            label=NoEscape(r"$\lambda_f$"),
            description=NoEscape(r"Raz\~ao de esbeltez do flange"),
        )
    )
    web_slenderness: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=2,
            label=NoEscape(r"$\lambda_w$"),
            description=NoEscape(r"Raz\~ao de esbeltez da alma"),
        )
    )
    slender_limit_ratio: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=2,
            label=NoEscape(r"$\alpha_p$"),
            description=NoEscape(
                r"Limite de esbeltez esbelto/(n\~ao esbelto ou n\~ao compacto)"
            ),
        )
    )
    compact_limit_ratio: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=2,
            label=NoEscape(r"$\alpha_r$"),
            description=NoEscape(r"Limite de esbeltez compacto/n\~ao compacto"),
        )
    )
    web_height: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="mm",
            round_precision=2,
            label=NoEscape(r"$w_h$"),
            description="Altura da alma",
        )
    )
    web_thickness: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="mm",
            round_precision=2,
            label=NoEscape(r"$t_w$"),
            description="Espessura da alma",
        )
    )
    total_height: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="mm",
            round_precision=0,
            label=NoEscape(r"$d$"),
            description="Altura total do perfil",
        )
    )
    distance_between_centroids: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="mm",
            round_precision=2,
            label=NoEscape(r"$h_0$"),
            description=NoEscape(r"Dist\^ancia entre centro\'ides dos flanges"),
        )
    )
    coefficient_c: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=1,
            label=NoEscape(r"$c$"),
            description=NoEscape(r"Coeficiente $c$"),
        )
    )
    mod_factor: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=1,
            label=NoEscape(r"$C_b$"),
            description=NoEscape(
                r"Coeficiente de modifica\c{c}\~ao de flambagem lateral torsional"
            ),
        )
    )
    lateral_torsional_buckling_modification_factor: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            round_precision=1,
            label=NoEscape(r"$C_b$"),
            description=NoEscape(
                r"Coeficiente de modifica\c{c}\~ao de flambagem lateral torsional"
            ),
        )
    )
    area: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 2",
            round_precision=2,
            label=NoEscape(r"$A_g$"),
            description=NoEscape(r"\'Area bruta da se\c{c}\~ao transversal"),
        )
    )
    major_axis_inertia: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 4",
            round_precision=0,
            label=NoEscape(r"$I_x$"),
            description=NoEscape(r"Momento de in\'ercia do eixo principal"),
        )
    )
    minor_axis_inertia: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 4",
            round_precision=0,
            label=NoEscape(r"$I_y$"),
            description=NoEscape(r"Momento de in\'ercia do eixo secund\'ario"),
        )
    )
    major_axis_elastic_section_modulus: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 3",
            round_precision=0,
            label=NoEscape(r"$S_x$"),
            description=NoEscape(r"Momento de in\'ercia el\'astico do eixo principal"),
        )
    )
    major_axis_plastic_section_modulus: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 3",
            round_precision=0,
            label=NoEscape(r"$Z_x$"),
            description=NoEscape(r"Momento de in\'ercia do eixo principal"),
        )
    )
    major_axis_radius_of_gyration: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm",
            round_precision=2,
            label=NoEscape(r"$r_x$"),
            description=NoEscape(r"Raio de gira\c{c}\~ao do eixo principal"),
        )
    )
    minor_axis_elastic_section_modulus: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 3",
            round_precision=0,
            label=NoEscape(r"$S_y$"),
            description=NoEscape(
                r"Momento de in\'ercia el\'astico do eixo secund\'ario"
            ),
        )
    )
    minor_axis_plastic_section_modulus: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 3",
            round_precision=0,
            label=NoEscape(r"$Z_y$"),
            description=NoEscape(r"Momento de in\'ercia do eixo secund\'ario"),
        )
    )
    minor_axis_radius_of_gyration: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm",
            round_precision=2,
            label=NoEscape(r"$r_y$"),
            description=NoEscape(r"Raio de gira\c{c}\~ao do eixo secund\'ario"),
        )
    )
    effective_radius_of_gyration: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm",
            round_precision=2,
            label=NoEscape(r"$r_{ts}$"),
            description=NoEscape(r"Raio de gira\c{c}\~ao efetivo"),
        )
    )
    torsional_constant: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 4",
            round_precision=0,
            label=NoEscape(r"$J$"),
            description=NoEscape(r"Momento Polar de In\'ercia"),
        )
    )
    torsional_radius_of_gyration: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm",
            round_precision=2,
            label=NoEscape(r"$r_z$"),
            description=NoEscape(r"Raio de gira\c{c}\~ao torsional"),
        )
    )
    warping_constant: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            print_units="cm ** 6",
            round_precision=0,
            label=NoEscape(r"$C_w$"),
            description=NoEscape(r"Constante de \emph{warping}"),
        )
    )
    construction: PrintOptions = field(
        default_factory=partial(
            PrintOptions, label="-", description=NoEscape(r"Tipo de constru\c{c}\~ao")
        )
    )
    factor_k: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"$K$"),
            round_precision=1,
            description="Fator de comprimento efetivo (flambagem)",
        )
    )
    factor_k_minor_axis: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"$K_y$"),
            round_precision=1,
            description=NoEscape(
                r"Fator de comprimento efetivo (flambagem) eixo secund\'ario"
            ),
        )
    )
    factor_k_major_axis: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"$K_x$"),
            round_precision=1,
            description=NoEscape(
                r"Fator de comprimento efetivo (flambagem) eixo principal"
            ),
        )
    )
    unbraced_length: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"$L_b$"),
            round_precision=0,
            print_units="mm",
            description="Comprimento entre suportes da viga",
        )
    )
    minor_axis_slenderness: PrintOptions = field(
        default_factory=partial(PrintOptions, round_precision=2)
    )
    slenderness_limit: PrintOptions = field(
        default_factory=partial(PrintOptions, round_precision=2)
    )
    elastic_buckling_critical_stress: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"F_e"),
            round_precision=2,
            print_units="MPa",
            description=NoEscape(r"Tens\~ao cr\'itica de flambagem elástica"),
        )
    )
    critical_stress: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"F_{cr}"),
            round_precision=2,
            print_units="MPa",
            description=NoEscape(r"Tens\~ao cr\'itica"),
        )
    )
    strength_force: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"P_{n}"),
            round_precision=2,
            print_units="kN",
            description=NoEscape(r"Carga cr\'itica nomimal"),
        )
    )

    required_axial_strength: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"P_{r}"),
            round_precision=2,
            print_units="kN",
            description=NoEscape(r"Carga axial aplicada"),
        )
    )
    required_major_axis_flexural_strength: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"M_{rx}"),
            round_precision=2,
            print_units="kN*m",
            description=NoEscape(r"Momento fletor aplicado - eixo principal"),
        )
    )
    required_minor_axis_flexural_strength: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"M_{ry}"),
            round_precision=2,
            print_units="kN*m",
            description=NoEscape(r"Momento fletor aplicado - eixo secund\'ario"),
        )
    )
    strength_moment: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"M_{n}"),
            round_precision=2,
            print_units="kN*m",
            description=NoEscape(r"Momento cr\'itica nomimal"),
        )
    )
    limit_length_flexural_yield: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"L_p"),
            round_precision=0,
            description="Comprimento limite em flexão para o caso de escoamento ",
            print_units="mm",
        )
    )
    limit_length_flexural_lateral_torsional_buckling: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"L_r"),
            round_precision=0,
            description=NoEscape(
                "Comprimento limite em flex\~ao para o caso de flambagem lateral tosrional"
            ),
            print_units="mm",
        )
    )
    criteria: PrintOptions = field(
        default_factory=partial(PrintOptions, round_precision=2)
    )
    nominal_shear_strength: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"V{n}"),
            round_precision=2,
            print_units="kN",
            description=NoEscape(r"Força Cortante Limite Nominal"),
        )
    )
    design_shear_strength: PrintOptions = field(
        default_factory=partial(
            PrintOptions,
            label=NoEscape(r"V{c}"),
            round_precision=2,
            print_units="kN",
            description=NoEscape(r"Força Cortante Limite de Projeto"),
        )
    )

    def to_dict(self):
        return {field_.name: getattr(self, field_.name) for field_ in fields(self)}


config_dict = ReportConfig()
