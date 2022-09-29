from quantities import UnitQuantity, Quantity, GPa, MPa, cm, m, mm, N

from structure_scripts.aisc_360_10.elements import (
    BeamCompressionFlexuralBuckling,
    BeamFlexureDoublySymmetric,
    BeamShearWeb,
    BeamCompressionTorsionalBuckling, BeamModel
)
from structure_scripts.aisc_360_10.sections import AreaProperties, GenericAreaPropertiesWithWeb
from structure_scripts.aisc_360_10.i_profile import DoublySymmetricIDimensionsUserDefined, DoublySymmetricI
from structure_scripts.aisc_360_10.channel import ChannelDimensions, ChannelAreaProperties
from structure_scripts.aisc_360_10.helpers import ConstructionType
from structure_scripts.shared.helpers import same_units_simplify
from structure_scripts.shared.materials import IsoTropicMaterial, steel

dm = UnitQuantity("decimeter", 0.1 * m, symbol="dm")
kN = UnitQuantity("kilo newton", 1000 * N, symbol="kN")
MN = UnitQuantity("mega newton", 1000000 * N, symbol="MN")

# Doubly symmetric I profiles
area_properties_127x76x13 = GenericAreaPropertiesWithWeb(
    area=16.5 * cm ** 2,
    web_area=447.2 * mm ** 2,
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
# channel profiles
channel_1_dimensions = ChannelDimensions(
    total_height=100 * mm,
    web_thickness=10 * mm,
    flange_thickness=10 * mm,
    flange_width=50 * mm,
)
channel_1_area_properties = ChannelAreaProperties(dimensions=channel_1_dimensions)

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

beam_model = BeamModel(
    profile=profile_200x10_200x10,
    unbraced_length_major_axis=1.0*m
)
print(beam_model.shear_major_axis_strengths)