from structure_scripts.aisc_360_10.elements import (
    DoublySymmetricI,
    GenericAreaProperties,
    BeamCompressionEffectiveLength,
    BeamFlexureDoublySymmetric,
    DoublySymmetricIDimensionsUserDefined, BeamShearWeb, BeamTorsionEffectiveLength
)
from structure_scripts.shared.materials import IsoTropicMaterial

from structure_scripts.aisc_360_10.helpers import same_units_simplify, Slenderness, ConstructionType
from pytest import approx, mark
from quantities import UnitQuantity, Quantity, GPa, MPa, cm, m, mm, N

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilo newton", 1000 * N, symbol="kN")
MN = UnitQuantity("mega newton", 1000000 * N, symbol="MN")

steel = IsoTropicMaterial(
    modulus_linear=200 * GPa,
    modulus_shear=77 * GPa,
    poisson_ratio=0.3,
    yield_stress=355 * MPa
)
area_properties_127x76x13 = GenericAreaProperties(
    area=16.5 * cm ** 2,
    minor_axis_inertia=56 * cm ** 4,
    minor_axis_elastic_section_modulus=15 * cm ** 3,
    major_axis_inertia=473 * cm ** 4,
    major_axis_elastic_section_modulus=75 * cm ** 3,
    major_axis_plastic_section_modulus=84 * cm ** 3,
    torsional_constant=2.85 * cm ** 4,
    warping_constant=2000000000 * mm ** 6
)
dimensions_127x76x13 = DoublySymmetricIDimensionsUserDefined(
    flange_width=76 * mm,
    flange_thickness=7.6 * mm,
    web_thickness=4 * mm,
    web_radii=7.6 * mm,
    total_height=127 * mm
)
dimensions_200x10_200x10 = DoublySymmetricIDimensionsUserDefined(
    flange_width=200 * mm,
    flange_thickness=10 * mm,
    web_thickness=10 * mm,
    total_height=220 * mm
)
profile_127x76x13_rolled = DoublySymmetricI(
    area_properties=area_properties_127x76x13,
    dimensions=dimensions_127x76x13,
    material=steel

)
profile_200x10_200x10 = DoublySymmetricI(
    dimensions=dimensions_200x10_200x10,
    material=steel

)
profile_built_up = DoublySymmetricI(
    area_properties=area_properties_127x76x13,
    dimensions=dimensions_127x76x13,
    material=steel,
    construction=ConstructionType.BUILT_UP
)
beam_1_compression = BeamCompressionEffectiveLength(
    profile=profile_127x76x13_rolled,
    unbraced_length_major_axis =1.0 * m,
)
beam_1_torsion = BeamTorsionEffectiveLength(
    profile=profile_127x76x13_rolled,
    unbraced_length=1.0*m
)
beam_1_flexure = BeamFlexureDoublySymmetric(
    profile=profile_127x76x13_rolled,
    unbraced_length=1.0 * m
)
beam_shear_web_1 = BeamShearWeb(profile=profile_200x10_200x10)
beam_shear_web_1_shear_nominal_strength = Quantity(426 * kN)


@mark.parametrize(
    "profile",
    [
        (profile_built_up, 0.76)
    ]
)
def test_doubly_symmetric_i_kc_coefficient(
        profile: tuple[DoublySymmetricI, float]
):
    assert (profile[0].slenderness.flange.kc_coefficient == approx(profile[1]))


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 21.12388887 * mm),
    ]
)
def test_doubly_symmetric_i_effective_radius_of_gyration(
        profile: tuple[DoublySymmetricI, Quantity]
):
    calculated, reference = same_units_simplify(profile[0].effective_radius_of_gyration, profile[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 2912.384214 * mm),
    ]
)
def test_doubly_symmetric_i_limit_length_torsional_buckling(
        profile: tuple[DoublySymmetricI, Quantity]
):
    calculated, reference = same_units_simplify(profile[0].limit_length_torsional_buckling, profile[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 769.6008355 * mm),
    ]
)
def test_doubly_symmetric_i_limit_length_yield(
        profile: tuple[DoublySymmetricI, Quantity]
):
    calculated, reference = same_units_simplify(profile[0].limit_length_yield, profile[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 13.29195457),
        (profile_built_up, 13.24303697)
    ]
)
def test_doubly_symmetric_i_flange_axial_slenderness_limit(
        profile: tuple[DoublySymmetricI, float]
):
    assert (profile[0].slenderness.flange.axial_compression.limit_ratio == approx(profile[1]))


def test_doubly_symmetric_i_web_axial_slenderness_limit():
    assert (profile_127x76x13_rolled.slenderness.web.axial_compression.limit_ratio == approx(35.36609341))


def test_doubly_symmetric_i_flange_flexural_slenderness_limit():
    assert (profile_127x76x13_rolled.slenderness.flange.axial_limit_ratio == approx(13.29195457))


def test_doubly_symmetric_i_web_flexural_limit():
    assert (profile_127x76x13_rolled.slenderness.web.axial_compression_limit_ratio == approx(35.36609341))


@mark.parametrize(
    "beam",
    [(beam_1_compression, 54.28101483)]
)
def test_beam_compression_effective_length_minor_axis_flexural_slenderness(
        beam: tuple[BeamCompressionEffectiveLength, float]
):
    assert beam[0].minor_axis_slenderness == approx(beam[1])


@mark.parametrize(
    "beam",
    [(beam_1_compression, Quantity(669.9367836, MPa))]
)
def test_beam_compression_effective_length_elastic_flexural_buckling_stress(
        beam: tuple[BeamCompressionEffectiveLength, Quantity]
):
    calculated, reference = same_units_simplify(beam[0].elastic_flexural_buckling_stress_minor_axis, beam[1])
    assert (calculated == approx(reference))


@mark.parametrize(
    "beam",
    [(beam_1_compression, Quantity(284.3846289, MPa))]
)
def test_beam_compression_effective_length_flexural_buckling_critical_stress(
        beam: tuple[BeamCompressionEffectiveLength, Quantity]
):
    calculated, reference = same_units_simplify(beam[0].flexural_buckling_critical_stress_minor_axis, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_compression, Quantity(469234.6376, N))]
)
def test_beam_compression_effective_length_flexural_buckling_strength(
        beam: tuple[BeamCompressionEffectiveLength, Quantity]
):
    calculated, reference = same_units_simplify(beam[0].strength_flexural_buckling, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_torsion, Quantity(1018.305052, MPa))]
)
def test_beam_compression_effective_length_torsional_buckling_elastic_stress(
        beam: tuple[BeamTorsionEffectiveLength, Quantity]
):
    calculated, reference = same_units_simplify(beam[0].critical_stress, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_torsion, Quantity(1680203.335, N))]
)
def test_beam_compression_effective_length_torsional_buckling_strength(
        beam: tuple[BeamTorsionEffectiveLength, Quantity]
):
    calculated, reference = same_units_simplify(beam[0].nominal_strength, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_flexure, Quantity(29820000, N * mm))]
)
def test_beam_flexure_yield_strength(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
    calculated, reference = same_units_simplify(beam[0].strength_major_axis_yield, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_flexure, Quantity(28617620.57, N * mm))]
)
def test_beam_flexure_strength_lateral_torsion_compact_case_b(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
    calculated, reference = same_units_simplify(beam[0].strength_lateral_torsion_compact_case_b, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_flexure, Quantity(1098.821625, MPa))]
)
def test_beam_flexure_critical_stress_lateral_torsional_buckling(
        beam: tuple[BeamFlexureDoublySymmetric,
                    Quantity]
):
    calculated, reference = same_units_simplify(beam[0].critical_stress_lateral_torsional_buckling, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_flexure, Quantity(82411621.84, N * mm))]
)
def test_beam_flexure_strength_lateral_torsion_compact_case_c(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
    calculated, reference = same_units_simplify(beam[0].strength_lateral_torsion_compact_case_c, beam[1])
    assert calculated == approx(reference)


@mark.parametrize(
    "beam",
    [(beam_1_flexure, Quantity(15583121.77, N * mm))]
)
def test_beam_flexure_strength_non_compact_flange_local_buckling(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
    calculated, reference = same_units_simplify(beam[0].strength_major_axis_flange_local_buckling_non_compact, beam[1])
    assert calculated == approx(reference)

@mark.parametrize(
    "beam",
    [(beam_shear_web_1, beam_shear_web_1_shear_nominal_strength)]
)
def test_beam_web_shear(beam: tuple[BeamShearWeb, Quantity]):
    calculated, reference = same_units_simplify(beam[0].nominal_strength, beam[1])
    assert calculated == approx(reference)
