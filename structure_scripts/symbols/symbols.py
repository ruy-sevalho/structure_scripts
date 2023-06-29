from sympy import var, Expr, latex, Symbol


nominal_strength = var("R_n")
nominal_stress = var("F_n")
nominal_body_area = var("A_b")
ultimate_stress = var("F_u")
yield_stress = var("F_y")
nominal_tensile_stress = var("F_nt")
nominal_shear_stress = var("F_nv")
base_metal_nominal_stress = var("F_nBM")
weld_nominal_stress = var("F_nw")
filler_metal_strength = var("F_EXX")
cross_sectional_area_base_metal = var("A_BM")
effective_weld_area = var("A_we")
effective_net_area = var("A_E")
gross_area = var("A_g")
net_shear_area = var("A_nv")
net_tension_area = var("A_nt")
gross_shear_area = var("A_gv")
Omega = var("Omega")
phi = var("phi")
theta = var("theta")
tension_distribution_factor = var("U_bs")
weld_size = var("D")
weld_length = var("l")
required_tensile_stress = var("f_rt")
required_shear_stress = var("f_rv")
bolt_diameter = var("d")
clear_distance = var("l_c")
thickness = var("t")
dim_y_hol = var("dy_h")
dim_y_col = var("dy_c")
dim_z_hol = var("dz_h")
dim_z_col = var("dz_c")
force1 = var("F_1")
force2 = var("F_2")
column_axial_load = var("P")
moment_y = var("M_y")
moment_z = var("M_z")
shear_y = var("S_y")
shear_z = var("S_z")


def _expression(
    nominal_stress: float | Symbol = nominal_stress,
    nominal_body_area: float | Symbol = nominal_body_area,
) -> float | Expr:
    return nominal_stress * nominal_body_area


if __name__ == "__main__":
    print(latex(_expression()))
    print(_expression(10.0, 10.0))
