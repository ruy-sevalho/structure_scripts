from dataclasses import dataclass

from quantities import UnitQuantity, cm, m, mm, N

from structure_scripts.aisc_360_10.beams import (
    BeamAnalysis,
    Beam,
    BucklingParam,
)
from structure_scripts.aisc_360_10.i_profile import (
    DoublySymmetricIDimensionsUserDefined,
    DoublySymmetricI,
)
from structure_scripts.aisc_360_10.channel import (
    ChannelDimensions,
    ChannelAreaProperties,
)
from structure_scripts.aisc_360_10.helpers import ConstructionType
from structure_scripts.materials import (
    steel355mpa,
)
from structure_scripts.sections import DirectInputAreaProperties

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilo newton", 1000 * N, symbol="kN")
MN = UnitQuantity("mega newton", 1000000 * N, symbol="MN")

# Doubly symmetric I profiles
area_properties_127x76x13 = DirectInputAreaProperties(
    area=16.5 * cm**2,
    minor_axis_inertia=56 * cm**4,
    minor_axis_elastic_section_modulus=15 * cm**3,
    major_axis_inertia=473 * cm**4,
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
channel_1_area_properties = ChannelAreaProperties(
    dimensions=channel_1_dimensions
)

# beam analysis
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
#     unbraced_length_major_axis=1.0*m
# )
# beam_param = BeamParameters(
#     unbraced_length_major_axis=1.0*m,
# )
beam_analysis = BeamAnalysis(
    section=profile_built_up,
    beam=Beam(buckling_param=BucklingParam(length_major_axis=1 * m)),
)
NAME = "name"


@dataclass
class TestInner:
    @property
    def name(self):
        return "name"


@dataclass
class Test:
    t: TestInner

    @property
    def name(self):
        return self.t.name


ti = TestInner
t = Test(ti)
n = t.name
