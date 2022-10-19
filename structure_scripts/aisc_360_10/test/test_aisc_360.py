from pytest import approx, mark, raises
from quantities import UnitQuantity, Quantity, GPa, MPa, cm, m, mm, N

from structure_scripts.aisc_360_10.compression_criteria import (
    FLEXURAL_BUCKLING_MAJOR,
    FlexuralBucklingAdaptor,
    FLEXURAL_BUCKLING_MINOR,
)
from structure_scripts.aisc_360_10.elements import (
    BeamCompressionFlexuralBuckling,
    BeamFlexureDoublySymmetric,
    BeamShearWeb,
    BeamCompressionTorsionalBuckling,
)
from structure_scripts.aisc_360_10.shear_criteria import SHEAR_STRENGTH
from structure_scripts.shared.sections import (
    AreaProperties,
    DirectInputAreaProperties,
)
from structure_scripts.aisc_360_10.sections import GenericAreaProperties
from structure_scripts.aisc_360_10.i_profile import (
    DoublySymmetricIDimensionsUserDefined,
    DoublySymmetricI,
)
from structure_scripts.aisc_360_10.channel import (
    ChannelDimensions,
    ChannelAreaProperties,
)
from structure_scripts.aisc_360_10.helpers import ConstructionType
from structure_scripts.shared.helpers import same_units_simplify
from structure_scripts.shared.materials import (
    IsotropicIsotropicMaterialUserDefined,
    steel355mpa,
)
from structure_scripts.aisc_360_10.beams import (
    BeamAnalysis,
    BucklingParam,
    Beam,
)

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilo newton", 1_000 * N, symbol="kN")
MN = UnitQuantity("mega newton", 1_000_000 * N, symbol="MN")

# Doubly symmetric I profiles
area_properties_127x76x13 = DirectInputAreaProperties(
    area=16.5 * cm**2,
    major_axis_inertia=473 * cm**4,
    minor_axis_inertia=56 * cm**4,
    minor_axis_elastic_section_modulus=15 * cm**3,
    major_axis_elastic_section_modulus=75 * cm**3,
    major_axis_plastic_section_modulus=84 * cm**3,
    polar_inertia=2.85 * cm**4,
    warping_constant=2000000000 * mm**6,
)
dimensions_127x76x13 = DoublySymmetricIDimensionsUserDefined(
    flange_width=76 * mm,
    flange_thickness=7.6 * mm,
    web_thickness=4 * mm,
    web_radii=7.6 * mm,
    total_height=127 * mm,
)
dimensions_200x10_200x10 = DoublySymmetricIDimensionsUserDefined(
    flange_width=200 * mm,
    flange_thickness=10 * mm,
    web_thickness=10 * mm,
    total_height=220 * mm,
)
profile_127x76x13_rolled = DoublySymmetricI(
    area_properties=area_properties_127x76x13,
    dimensions=dimensions_127x76x13,
    material=steel355mpa,
)
profile_200x10_200x10 = DoublySymmetricI(
    dimensions=dimensions_200x10_200x10, material=steel355mpa
)
profile_built_up = DoublySymmetricI(
    area_properties=area_properties_127x76x13,
    dimensions=dimensions_127x76x13,
    material=steel355mpa,
    construction=ConstructionType.BUILT_UP,
)

# channel profiles
channel_1_dimensions = ChannelDimensions(
    total_height=100 * mm,
    web_thickness=10 * mm,
    flange_thickness=10 * mm,
    flange_width=50 * mm,
)
channel_1_area_properties = ChannelAreaProperties(dimensions=channel_1_dimensions)

# beam analysis
beam_200x10_analysis = BeamAnalysis(
    section=profile_200x10_200x10,
    beam=Beam(
        buckling_param=BucklingParam(length_major_axis=1.0 * m),
    ),
)
beam_127x76x13_rolled_1m = BeamAnalysis(
    section=profile_127x76x13_rolled,
    beam=Beam(
        buckling_param=BucklingParam(length_major_axis=1.0 * m),
    ),
)
beam_127x76x13_rolled_2m = BeamAnalysis(
    section=profile_127x76x13_rolled,
    beam=Beam(
        buckling_param=BucklingParam(length_major_axis=2.0 * m),
    ),
)
beam_127x76x13_rolled_4m = BeamAnalysis(
    section=profile_127x76x13_rolled,
    beam=Beam(
        buckling_param=BucklingParam(length_major_axis=4.0 * m),
    ),
)

# beam_1_compression_flexural_buckling = BeamCompressionFlexuralBuckling(
#     profile=profile_127x76x13_rolled,
#     unbraced_length_major_axis=1.0 * m,
# )
# beam_1_compression_torsional_buckling = BeamCompressionTorsionalBuckling(
#     profile=profile_127x76x13_rolled,
#     unbraced_length=1.0 * m,
# )
# beam_2_compression_flexural_buckling = BeamCompressionFlexuralBuckling(
#     profile=profile_127x76x13_rolled,
#     unbraced_length_major_axis=2.0 * m,
# )
# beam_2_compression_torsional_buckling = BeamCompressionTorsionalBuckling(
#     profile=profile_127x76x13_rolled,
#     unbraced_length=2.0 * m,
# )
# beam_3_compression_flexural_buckling = BeamCompressionFlexuralBuckling(
#     profile=profile_127x76x13_rolled,
#     unbraced_length_major_axis=4.0 * m,
# )
# beam_3_compression_torsional_buckling = BeamCompressionTorsionalBuckling(
#     profile=profile_127x76x13_rolled,
#     unbraced_length=4.0 * m,
# )
# beam_1_flexure = BeamFlexureDoublySymmetric(
#     profile=profile_127x76x13_rolled,
#     unbraced_length_major_axis=1.0 * m
# )
# beam_shear_web_1 = BeamShearWeb(profile=profile_200x10_200x10)
# beam_shear_web_1_shear_nominal_strength = Quantity(426 * kN)
# beam_model = BeamModel(
#     profile=profile_200x10_200x10,
#     unbraced_length_major_axis=1.0 * m
# )


@mark.parametrize("profile", [(profile_built_up, 0.76)])
def test_doubly_symmetric_i_kc_coefficient(profile: tuple[DoublySymmetricI, float]):
    assert profile[0].slenderness.flange.kc_coefficient == approx(profile[1])


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 21.12388887 * mm),
    ],
)
def test_doubly_symmetric_i_effective_radius_of_gyration(
    profile: tuple[DoublySymmetricI, Quantity]
):
    calculated, reference = same_units_simplify(
        profile[0].effective_radius_of_gyration, profile[1]
    )
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 2912.384214 * mm),
    ],
)
def test_doubly_symmetric_i_limit_length_torsional_buckling(
    profile: tuple[DoublySymmetricI, Quantity]
):
    calculated, reference = same_units_simplify(
        profile[0].limit_length_torsional_buckling, profile[1]
    )
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [
        (profile_127x76x13_rolled, 769.6008355 * mm),
    ],
)
def test_doubly_symmetric_i_limit_length_yield(
    profile: tuple[DoublySymmetricI, Quantity]
):
    calculated, reference = same_units_simplify(
        profile[0].limit_length_yield, profile[1]
    )
    assert calculated == approx(reference)


@mark.parametrize(
    "profile",
    [(profile_127x76x13_rolled, 13.29195457), (profile_built_up, 13.24303697)],
)
def test_doubly_symmetric_i_flange_axial_slenderness_limit(
    profile: tuple[DoublySymmetricI, float]
):
    assert profile[0].slenderness.flange.axial_compression.limit_ratio == approx(
        profile[1]
    )


def test_doubly_symmetric_i_web_axial_slenderness_limit():
    assert (
        profile_127x76x13_rolled.slenderness.web.axial_compression.limit_ratio
        == approx(35.36609341)
    )


def test_doubly_symmetric_i_flange_flexural_slenderness_limit():
    assert profile_127x76x13_rolled.slenderness.flange.axial_limit_ratio == approx(
        13.29195457
    )


def test_doubly_symmetric_i_web_flexural_limit():
    assert (
        profile_127x76x13_rolled.slenderness.web.axial_compression_limit_ratio
        == approx(35.36609341)
    )


@mark.parametrize(
    "beam, minor_axis_slenderness", [(beam_127x76x13_rolled_1m, 54.28101483)]
)
def test_beam_compression_effective_length_minor_axis_flexural_slenderness(
    beam: BeamAnalysis, minor_axis_slenderness: float
):
    flexural_buckling_criteria: FlexuralBucklingAdaptor = beam.compression[
        FLEXURAL_BUCKLING_MINOR
    ]
    assert flexural_buckling_criteria.beam_slenderness == approx(minor_axis_slenderness)


@mark.parametrize(
    "beam, elastic_stress",
    [(beam_127x76x13_rolled_1m, Quantity(669.9367836, MPa))],
)
def test_minor_axis_flexural_buckling_elastic_stress(
    beam: BeamAnalysis, elastic_stress: Quantity
):
    flexural_buckling_criteria: FlexuralBucklingAdaptor = beam.compression[
        FLEXURAL_BUCKLING_MINOR
    ]
    calculated, reference = same_units_simplify(
        flexural_buckling_criteria.elastic_buckling_stress, elastic_stress
    )
    assert calculated == approx(reference)


@mark.parametrize(
    "beam, critical_stress",
    [(beam_127x76x13_rolled_1m, Quantity(284.3846289, MPa))],
)
def test_beam_compression_effective_length_flexural_buckling_critical_stress(
    beam: BeamAnalysis, critical_stress: Quantity
):
    flexural_buckling_criteria: FlexuralBucklingAdaptor = beam.compression[
        FLEXURAL_BUCKLING_MINOR
    ]
    calculated, reference = same_units_simplify(
        flexural_buckling_criteria.critical_stress, critical_stress
    )
    assert calculated == approx(reference)


@mark.parametrize(
    "beam, nominal_buckling_strength",
    [
        (beam_127x76x13_rolled_1m, Quantity(469234.6376, N)),
        (beam_127x76x13_rolled_2m, Quantity(241225.5807, N)),
        (beam_127x76x13_rolled_4m, Quantity(60589.50142, N)),
    ],
)
def test_beam_compression_effective_length_flexural_buckling_strength(
    beam: BeamAnalysis, nominal_buckling_strength: Quantity
):

    calculated, reference = same_units_simplify(
        beam.compression.design_strength, nominal_buckling_strength
    )
    assert calculated == approx(reference)


#
# @mark.parametrize(
#     "beam",
#     [
#         (beam_1_compression_torsional_buckling, Quantity(312.3582787, MPa)),
#         (beam_2_compression_torsional_buckling, Quantity(277.2878718, MPa))
#     ]
# )
# def test_beam_compression_effective_length_torsional_buckling_critical_stress(
#         beam: tuple[BeamCompressionTorsionalBuckling, Quantity]
# ):
#     calculated, reference = same_units_simplify(beam[0].torsional_critical_stress, beam[1])
#     assert calculated == approx(reference)
#
#
# @mark.parametrize(
#     "beam",
#     [
#         (beam_1_compression_torsional_buckling, Quantity(515391.1599, N)),
#         (beam_2_compression_torsional_buckling, Quantity(457524.9885, N)),
#         (beam_3_compression_torsional_buckling, Quantity(424502.8659, N))
#     ]
# )
# def test_beam_compression_effective_length_torsional_buckling_strength(
#         beam: tuple[BeamCompressionTorsionalBuckling, Quantity]
# ):
#     calculated, reference = same_units_simplify(beam[0].nominal_strength, beam[1])
#     assert calculated == approx(reference)
#
#
# @mark.parametrize(
#     "beam",
#     [(beam_1_flexure, Quantity(29820000, N * mm))]
# )
# def test_beam_flexure_yield_strength(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
#     calculated, reference = same_units_simplify(beam[0].strength_major_axis_yield, beam[1])
#     assert calculated == approx(reference)
#
#
# @mark.parametrize(
#     "beam",
#     [(beam_1_flexure, Quantity(28617620.57, N * mm))]
# )
# def test_beam_flexure_strength_lateral_torsion_compact_case_b(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
#     calculated, reference = same_units_simplify(beam[0].strength_lateral_torsion_compact_case_b, beam[1])
#     assert calculated == approx(reference)
#
#
# @mark.parametrize(
#     "beam",
#     [(beam_1_flexure, Quantity(1098.821625, MPa))]
# )
# def test_beam_flexure_critical_stress_lateral_torsional_buckling(
#         beam: tuple[BeamFlexureDoublySymmetric,
#                     Quantity]
# ):
#     calculated, reference = same_units_simplify(beam[0].critical_stress_lateral_torsional_buckling, beam[1])
#     assert calculated == approx(reference)
#
#
# @mark.parametrize(
#     "beam",
#     [(beam_1_flexure, Quantity(82411621.84, N * mm))]
# )
# def test_beam_flexure_strength_lateral_torsion_compact_case_c(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
#     calculated, reference = same_units_simplify(beam[0].strength_lateral_torsion_compact_case_c, beam[1])
#     assert calculated == approx(reference)
#
#
# @mark.parametrize(
#     "beam",
#     [(beam_1_flexure, Quantity(15583121.77, N * mm))]
# )
# def test_beam_flexure_strength_non_compact_flange_local_buckling(beam: tuple[BeamFlexureDoublySymmetric, Quantity]):
#     calculated, reference = same_units_simplify(beam[0].strength_major_axis_flange_local_buckling_non_compact, beam[1])
#     assert calculated == approx(reference)
#
#


@mark.parametrize(
    "beam, expected_nominal_strength_shear_major_axis",
    [(beam_200x10_analysis, Quantity(426 * kN))],
)
def test_beam_web_shear_nominal_strength(
    beam: BeamAnalysis, expected_nominal_strength_shear_major_axis: Quantity
):
    calculated, reference = same_units_simplify(
        beam.shear_major_axis[SHEAR_STRENGTH].nominal_strength,
        expected_nominal_strength_shear_major_axis,
    )
    assert calculated == approx(reference)


@mark.parametrize(
    "beam, expected_design_strength_shear_major_axis",
    [(beam_200x10_analysis, Quantity(284 * kN))],
)
def test_beam_web_shear_design_strength(
    beam: BeamAnalysis, expected_design_strength_shear_major_axis: Quantity
):
    # Only special case where the safety factor value is supposed to change
    calculated, reference = same_units_simplify(
        beam.shear_major_axis[SHEAR_STRENGTH].design_strength,
        expected_design_strength_shear_major_axis,
    )
    assert calculated == approx(reference)


def test_channel_dimensions_does_not_accept_total_and_web_height():
    with raises(ValueError):
        ChannelDimensions(
            flange_width=100 * mm,
            flange_thickness=10 * mm,
            web_height=100 * mm,
            web_thickness=10 * mm,
            total_height=100 * mm,
        )


def test_channel_dimensions_does_not_accept_no_height():
    with raises(ValueError):
        ChannelDimensions(
            flange_width=100 * mm,
            flange_thickness=10 * mm,
            web_thickness=10 * mm,
        )


@mark.parametrize(
    "web_height, flange_thickness, expected_total_height",
    [
        (100 * mm, 10 * mm, 120 * mm),
    ],
)
def test_channel_dimensions_calculates_correct_total_height(
    web_height: Quantity,
    flange_thickness: Quantity,
    expected_total_height: Quantity,
):
    channel = ChannelDimensions(
        web_height=web_height,
        flange_thickness=flange_thickness,
        web_thickness=1 * mm,
        flange_width=10 * mm,
    )
    assert channel.total_height == expected_total_height


@mark.parametrize(
    "total_height, flange_thickness, expected_web_height",
    [
        (100 * mm, 10 * mm, 80 * mm),
    ],
)
def test_channel_dimensions_calculates_correct_web_height(
    total_height: Quantity,
    flange_thickness: Quantity,
    expected_web_height: Quantity,
):
    channel = ChannelDimensions(
        total_height=total_height,
        flange_thickness=flange_thickness,
        web_thickness=1 * mm,
        flange_width=10 * mm,
    )
    assert channel.web_height == expected_web_height


@mark.parametrize(
    "channel, expected_area",
    [
        (channel_1_area_properties, 1800 * mm**2),
    ],
)
def test_channel_dimensions_area(channel: AreaProperties, expected_area: Quantity):
    assert channel.area == expected_area
