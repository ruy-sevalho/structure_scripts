from dataclasses import dataclass
from functools import cached_property, partial
from typing import Optional, Union, Protocol
from abc import abstractmethod

from quantities import Quantity

from structure_scripts.aisc_360_10.sections import AISC_360_10RuleCheck
from structure_scripts.section_properties import AreaProperties, ConstructionType
from structure_scripts.aisc_360_10.helpers import (
    web_height_from_total,
    doubly_symmetric_i_torsional_constant,
    doubly_symmetric_i_warping_constant,
    _total_height,
)
from structure_scripts.aisc_360_10.i_profile import DoublySymmetricIAISC36010
from structure_scripts.helpers import (
    radius_of_gyration,
    rectangle_area,
    self_inertia,
    transfer_inertia,
    section_modulus,
    areas_centroid,
)
from structure_scripts.materials import IsotropicMaterial


@dataclass(frozen=True)
class DoublySymmetricIDimensions:
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Quantity
    web_radii: Quantity = Quantity(0, "mm")

    @cached_property
    def web_height(self):
        return web_height_from_total(self.total_height, self.flange_thickness)

    @cached_property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness

    @cached_property
    def web_height_corrected(self):
        if self.web_radii:
            return self.web_height - 2 * self.web_radii
        else:
            return self.web_height


def new_doubly_symmetric_i_dimensions():
    # TODO implement dsi constructor here, removing initialization logic from dataclass
    pass


@dataclass(frozen=True)
class ChannelDimensions:
    """Channel section profile definition"""

    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    total_height: Quantity
    web_height: Quantity

    @cached_property
    def distance_between_centroids(self):
        return self.total_height - self.flange_thickness


def new_channel_dimensions(
    flange_width: Quantity,
    flange_thickness: Quantity,
    web_thickness: Quantity,
    total_height: Optional[Quantity] = None,
    web_height: Optional[Quantity] = None,
):
    """Creates a new ChannelDimension instance. Must specify either total height or web height but not both"""
    if total_height and web_height_from_total:
        raise ValueError(f"Pass either total or web height, but not both")
    if not total_height and not web_height_from_total:
        raise ValueError(
            "Must pass either total or web height, both can't be None"
        )
    if not total_height:
        total_height = _total_height(
            web_height=web_height,
            flange_thickness=flange_thickness,
        )
    else:
        web_height = web_height_from_total(
            total_height=total_height,
            flange_thickness=flange_thickness,
        )
    return ChannelDimensions(
        flange_width=flange_width,
        flange_thickness=flange_thickness,
        web_thickness=web_thickness,
        total_height=total_height,
        web_height=web_height,
    )


@dataclass
class _DoublySymmetricIandChannelBaseAreaProperties:
    dimensions: Union[DoublySymmetricIDimensions, ChannelDimensions]

    @cached_property
    def flange_area(self):
        return rectangle_area(
            width=self.dimensions.flange_width,
            height=self.dimensions.flange_thickness,
        )

    @cached_property
    def web_area(self):
        return rectangle_area(
            width=self.dimensions.web_thickness,
            height=self.dimensions.web_height,
        )

    @cached_property
    def area(self):
        return self.web_area + 2 * self.flange_area

    @cached_property
    def flange_self_inertia_major_axis(self):
        return self_inertia(
            width=self.dimensions.flange_width,
            height=self.dimensions.flange_thickness,
        )

    @cached_property
    def flange_self_inertia_minor_axis(self):
        return self_inertia(
            width=self.dimensions.flange_thickness,
            height=self.dimensions.flange_width,
        )

    @cached_property
    def web_self_inertia_major_axis(self):
        return self_inertia(
            width=self.dimensions.web_thickness,
            height=self.dimensions.web_height,
        )

    @cached_property
    def web_self_inertia_minor_axis(self):
        return self_inertia(
            width=self.dimensions.web_height,
            height=self.dimensions.web_thickness,
        )

    @cached_property
    def flange_area_centroid_major_axis(self):
        return self.dimensions.distance_between_centroids / 2

    @cached_property
    def flange_transfer_inertia_major_axis(self):
        return transfer_inertia(
            area=self.flange_area,
            center_to_na_distance=self.flange_area_centroid_major_axis,
        )

    @cached_property
    def minor_axis_inertia(self):
        return (
            2 * self.flange_self_inertia_minor_axis
            + self.web_self_inertia_minor_axis
        )

    @cached_property
    def major_axis_inertia(self):
        return (
            2 * self.flange_transfer_inertia_major_axis
            + 2 * self.flange_self_inertia_major_axis
            + self.web_self_inertia_major_axis
        )

    @cached_property
    def major_axis_elastic_section_modulus(self):
        return section_modulus(
            self.major_axis_inertia, self.dimensions.total_height / 2
        )

    @cached_property
    def minor_axis_elastic_section_modulus(self):
        return section_modulus(
            self.minor_axis_inertia, self.dimensions.flange_width / 2
        )

    @cached_property
    def major_axis_radius_of_gyration(self):
        return radius_of_gyration(
            moment_of_inertia=self.major_axis_inertia,
            gross_section_area=self.area,
        )

    @cached_property
    def minor_axis_radius_of_gyration(self):
        return radius_of_gyration(
            moment_of_inertia=self.minor_axis_inertia,
            gross_section_area=self.area,
        )

    @cached_property
    def major_axis_plastic_half_centroid(self):
        return areas_centroid(
            (
                (self.flange_area, self.flange_area_centroid_major_axis),
                (self.web_area / 2, self.dimensions.web_height / 4),
            )
        )

    @cached_property
    def major_axis_plastic_half_area(self):
        return self.flange_area + self.web_area / 2

    @cached_property
    def major_axis_plastic_section_modulus(self):
        return (
            2
            * self.major_axis_plastic_half_centroid
            * self.major_axis_plastic_half_area
        )

    @cached_property
    def minor_axis_plastic_half_centroid(self):
        return areas_centroid(
            (
                (self.flange_area, self.dimensions.flange_width / 4),
                (self.web_area / 2, self.dimensions.web_thickness / 4),
            )
        )

    @cached_property
    def minor_axis_plastic_half_area(self):
        return self.flange_area + self.web_area / 2

    @cached_property
    def minor_axis_plastic_section_modulus(self):
        return (
            2
            * self.minor_axis_plastic_half_area
            * self.minor_axis_plastic_half_centroid
        )


def _partial_area_prop_dsi_channel(
    base_area_prop: _DoublySymmetricIandChannelBaseAreaProperties,
):
    return partial(
        AreaProperties,
        area=base_area_prop.area,
        major_axis_inertia=base_area_prop.major_axis_inertia,
        minor_axis_inertia=base_area_prop.minor_axis_inertia,
        major_axis_elastic_section_modulus=base_area_prop.major_axis_elastic_section_modulus,
        minor_axis_elastic_section_modulus=base_area_prop.minor_axis_elastic_section_modulus,
        major_axis_plastic_section_modulus=base_area_prop.major_axis_plastic_section_modulus,
        minor_axis_plastic_section_modulus=base_area_prop.minor_axis_plastic_section_modulus,
        major_axis_radius_of_gyration=base_area_prop.major_axis_radius_of_gyration,
        minor_axis_radius_of_gyration=base_area_prop.minor_axis_radius_of_gyration,
    )


def channel_area_properties(dimensions: DoublySymmetricIDimensions):
    base_area_prop = _DoublySymmetricIandChannelBaseAreaProperties(dimensions)
    polar_inertia = doubly_symmetric_i_torsional_constant(
        flange_width=dimensions.flange_width,
        total_height=dimensions.total_height,
        flange_thickness=dimensions.flange_thickness,
        web_thickness=dimensions.web_thickness,
    )
    polar_radius_of_gyration = radius_of_gyration(
        moment_of_inertia=polar_inertia,
        gross_section_area=base_area_prop.area,
    )
    warping_constant = (
        doubly_symmetric_i_warping_constant(
            moment_of_inertia=base_area_prop.minor_axis_inertia,
            distance_between_flanges_centroid=dimensions.distance_between_centroids,
        ),
    )


class SectionChecks(Protocol):
    @property
    @abstractmethod
    def aisc_360_10(self) -> AISC_360_10RuleCheck:
        pass


@dataclass(frozen=True)
class DoublySymmetricI:
    dimensions: DoublySymmetricIDimensions
    material: IsotropicMaterial
    area_properties: AreaProperties
    construction: ConstructionType = ConstructionType.ROLLED

    @cached_property
    def aisc_360_10(self):
        return DoublySymmetricIAISC36010(
            dimensions=self.dimensions,
            material=self.material,
            area_properties=self.area_properties,
            construction=self.construction
        )


def doubly_symmetric_i_area_properties(dimensions: DoublySymmetricIDimensions):
    base_area_prop = _DoublySymmetricIandChannelBaseAreaProperties(dimensions)
    polar_inertia = doubly_symmetric_i_torsional_constant(
        flange_width=dimensions.flange_width,
        total_height=dimensions.total_height,
        flange_thickness=dimensions.flange_thickness,
        web_thickness=dimensions.web_thickness,
    )
    polar_radius_of_gyration = radius_of_gyration(
        moment_of_inertia=polar_inertia,
        gross_section_area=base_area_prop.area,
    )
    warping_constant = (
        doubly_symmetric_i_warping_constant(
            moment_of_inertia=base_area_prop.minor_axis_inertia,
            distance_between_flanges_centroid=dimensions.distance_between_centroids,
        ),
    )
    return _partial_area_prop_dsi_channel(base_area_prop)(
        polar_inertia=polar_inertia,
        polar_radius_of_gyration=polar_radius_of_gyration,
        warping_constant=warping_constant,
    )


def create_doubly_symmetric_i(
    dimensions: DoublySymmetricIDimensions,
    material: IsotropicMaterial,
    area_properties: AreaProperties = None,
    construction: ConstructionType = ConstructionType.ROLLED,
) -> DoublySymmetricI:
    return DoublySymmetricI(
        dimensions=dimensions,
        material=material,
        area_properties=area_properties
        or doubly_symmetric_i_area_properties(dimensions),
        construction=construction,
    )


# return partial(
#     AreaProperties,
#     area=area,
#     major_axis_inertia=major_axis_inertia,
#     minor_axis_inertia=minor_axis_inertia,
#     major_axis_elastic_section_modulus=major_axis_elastic_section_modulus,
#     minor_axis_elastic_section_modulus=minor_axis_elastic_section_modulus,
#     major_axis_plastic_section_modulus=major_axis_plastic_section_modulus,
#     minor_axis_plastic_section_modulus=minor_axis_plastic_section_modulus,
#     major_axis_radius_of_gyration=major_axis_radius_of_gyration,
#     minor_axis_radius_of_gyration=minor_axis_radius_of_gyration,
# )


# def doubly_symmetric_i_section_properties(
#     dimensions: DoublySymmetricIDimensions,
# ):
#     flange_area = rectangle_area(
#         width=dimensions.flange_width,
#         height=dimensions.flange_thickness,
#     )
#     web_area = rectangle_area(
#         width=dimensions.web_thickness,
#         height=dimensions.web_height,
#     )
#     area = web_area + 2 * flange_area
#     # flange_self_inertia_major_axis = self_inertia(
#     #     width=dimensions.flange_width,
#     #     height=dimensions.flange_thickness,
#     # )
#     # flange_self_inertia_minor_axis = self_inertia(
#     #     width=dimensions.flange_thickness,
#     #     height=dimensions.flange_width,
#     # )
#     # web_self_inertia_major_axis = self_inertia(
#     #     width=dimensions.web_thickness,
#     #     height=dimensions.web_height,
#     # )
#     # web_self_inertia_minor_axis = self_inertia(
#     #     width=dimensions.web_height,
#     #     height=dimensions.web_thickness,
#     # )
#     # flange_area_centroid_major_axis = dimensions.distance_between_centroids / 2
#     # flange_transfer_inertia_major_axis = transfer_inertia(
#     #     area=flange_area,
#     #     center_to_na_distance=flange_area_centroid_major_axis,
#     # )
#     # minor_axis_inertia = (
#     #     2 * flange_self_inertia_minor_axis + web_self_inertia_minor_axis
#     # )
#     # major_axis_inertia = (
#     #     2 * flange_transfer_inertia_major_axis
#     #     + 2 * flange_self_inertia_major_axis
#     #     + web_self_inertia_major_axis
#     # )
#     # major_axis_elastic_section_modulus = section_modulus(
#     #     major_axis_inertia, dimensions.total_height / 2
#     # )
#     # minor_axis_elastic_section_modulus = section_modulus(
#     #     minor_axis_inertia, dimensions.flange_width / 2
#     # )
#     # major_axis_radius_of_gyration = radius_of_gyration(
#     #     moment_of_inertia=major_axis_inertia,
#     #     gross_section_area=area,
#     # )
#     # minor_axis_radius_of_gyration = radius_of_gyration(
#     #     moment_of_inertia=minor_axis_inertia,
#     #     gross_section_area=area,
#     # )
#     polar_inertia = doubly_symmetric_i_torsional_constant(
#         flange_width=dimensions.flange_width,
#         total_height=dimensions.total_height,
#         flange_thickness=dimensions.flange_thickness,
#         web_thickness=dimensions.web_thickness,
#     )
#     polar_radius_of_gyration = radius_of_gyration(
#         moment_of_inertia=polar_inertia,
#         gross_section_area=area,
#     )
#     # major_axis_plastic_half_centroid = areas_centroid(
#     #     (
#     #         (flange_area, flange_area_centroid_major_axis),
#     #         (web_area / 2, dimensions.web_height / 4),
#     #     )
#     # )
#     # major_axis_plastic_half_area = flange_area + web_area / 2
#     # major_axis_plastic_section_modulus = (
#     #     2 * major_axis_plastic_half_centroid * major_axis_plastic_half_area
#     # )
#     # minor_axis_plastic_half_centroid = areas_centroid(
#     #     (
#     #         (flange_area, dimensions.flange_width / 4),
#     #         (web_area / 2, dimensions.web_thickness / 4),
#     #     )
#     # )
#     # minor_axis_plastic_half_area = flange_area + web_area / 2
#     # minor_axis_plastic_section_modulus = (
#     #     2 * minor_axis_plastic_half_area * minor_axis_plastic_half_centroid
#     # )
#     return _doubly_symmetric_i_and_channel_common_section_properties(dimensions)(
#         warping_constant=warping_constant(
#             moment_of_inertia=minor_axis_inertia,
#             distance_between_flanges_centroid=dimensions.distance_between_centroids,
#         ),
#
#         polar_inertia=polar_inertia,
#     )
#
#
#
#
