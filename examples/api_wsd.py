from structure_scripts.shared.materials import IsoTropicMaterial, steel
from structure_scripts.api_rpa.elements import CircularSection, CircularSectionGeometry
from structure_scripts.api_rpa.elements_wsd import BeamModel
from quantities import Quantity, m, N, MPa, GPa, mm, inch

p4geo = CircularSectionGeometry(
    outer_diameter=(4.5 * inch).rescale(mm),
    wall_thickness=((4.5 - 4.029) * inch).rescale(mm)
)
p4 = CircularSection(
    geometry=p4geo,
    material=steel
)
beam = BeamModel(
    profile=p4,
)
results = beam.results(
    axial_force=10 ** 3 * N,
    bending_moment_x=1_000 * N * m,
    bending_moment_y=1_000 * N * m,
    torsion_moment=100 * N * m,
    shear_force=5_000 * N
)
results2 = beam.results(
    axial_force=-10 ** 3 * N,
    bending_moment_x=1_000 * N * m,
    bending_moment_y=1_000 * N * m,
    torsion_moment=100 * N * m,
    shear_force=5_000 * N
)
df = results.results
df2 = results2.results
print(df2.compression_bending_a)