from structure_scripts.api_rpa.elements_wsd import AxialCompression
from structure_scripts.api_rpa.elements import CircularSection, CircularSectionGeometry
from structure_scripts.shared.helpers import same_units_simplify
from structure_scripts.shared.materials import IsoTropicMaterial
from quantities import Quantity, N, m, mm, MPa, GPa, UnitQuantity
from pytest import approx, mark

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilo newton", 1000 * N, symbol="kN")
MN = UnitQuantity("mega newton", 1000000 * N, symbol="MN")

steel = IsoTropicMaterial(
    modulus_linear=200 * GPa,
    modulus_shear=77 * GPa,
    poisson_ratio=0.3,
    yield_stress=355 * MPa
)
circle_section_1 = CircularSectionGeometry(
    outer_diameter=50 * mm,
    wall_thickness=2 * mm
)
section_1 = CircularSection(
    geometry=circle_section_1,
    material=steel
)
compression_1 = AxialCompression(
    profile=section_1,
    length=1000 * mm
)


@mark.parametrize(
    "profile",
    [
        (circle_section_1, Quantity(21752.39113, 'mm')),
    ]
)
def test_radius_gyration(profile: tuple[CircularSectionGeometry, float]):
    calculated, reference = same_units_simplify(profile[0].radius_of_gyration, profile[1])
    assert calculated == approx(calculated)


@mark.parametrize(
    "profile",
    [
        (compression_1, 58.87448094),
    ]
)
def test_slenderness(profile: tuple[AxialCompression, float]):
    assert profile[0].slenderness == approx(profile[1])


@mark.parametrize(
    "profile",
    [
        (compression_1, 105.4546396),
    ]
)
def test_coef_c(profile: tuple[AxialCompression, float]):
    assert profile[0].coefficient_c == approx(profile[1])


@mark.parametrize(
    "profile",
    [
        (compression_1, 161.6130987 * MPa),
    ]
)
def test_compressive_stress_a(profile: tuple[AxialCompression, Quantity]):
    calculated, reference = same_units_simplify(profile[0].allowable_stress_a, profile[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (compression_1, 297.1180038 * MPa),
    ]
)
def test_compressive_stress_b(profile: tuple[AxialCompression, Quantity]):
    calculated, reference = same_units_simplify(profile[0].allowable_stress_b, profile[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (compression_1, 161.6130987 * MPa),
    ]
)
def test_compressive_stress(profile: tuple[AxialCompression, Quantity]):
    calculated, reference = same_units_simplify(profile[0].allowable_stress, profile[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [
        (compression_1, 10 * kN, 33.15727981 * MPa),
    ]
)
def test_acting_compressive_stress(beam: tuple[AxialCompression, Quantity, Quantity]):
    """First quantity is load applied and second expected stress"""
    calculated, reference = same_units_simplify(beam[0].acting_stress(load=beam[1]), beam[2])
    assert calculated == approx(reference)

