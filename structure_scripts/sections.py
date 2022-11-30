from dataclasses import dataclass
from functools import cached_property, partial
from typing import Optional, Union, Protocol
from abc import abstractmethod

from quantities import Quantity, m

from structure_scripts.aisc_360_10.channel import ChannelAISC36010
from structure_scripts.aisc_360_10.sections import AISC_360_10_Rule_Check
from structure_scripts.section_properties import (
    AreaProperties,
    ConstructionType,
)
from structure_scripts.aisc_360_10.helpers import (
    doubly_symmetric_i_warping_constant,
)
from structure_scripts.aisc_360_10.i_profile import DoublySymmetricIAISC36010
from structure_scripts.helpers import (
    radius_of_gyration,
    rectangle_area,
    self_inertia,
    transfer_inertia,
    section_modulus,
    areas_centroid,
    channel_corrected_dimensions,
    alpha,
    channel_torsional_constant,
    channel_warping_constant,
    polar_radius_of_gyration,
    ratio_simplify,
    minor_axis_plastic_section_modulus_i_channel,
)
from structure_scripts.materials import IsotropicMaterial


@dataclass(frozen=True)
class DoublySymmetricIDimensions:
    flange_width: Quantity
    flange_thickness: Quantity
    web_thickness: Quantity
    depth: Quantity
    web_radii: Quantity = Quantity(0, "mm")

    @cached_property
    def web_height(self):
        return web_height_from_total(self.depth, self.flange_thickness)

    @cached_property
    def distance_between_centroids(self):
        return self.depth - self.flange_thickness

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
    depth: Quantity

    @cached_property
    def distance_between_centroids(self):
        return self.depth - self.flange_thickness

    @cached_property
    def web_height(self):
        return web_height_from_total(self.depth, self.flange_thickness)


def new_channel_dimensions(
    flange_width: Quantity,
    flange_thickness: Quantity,
    web_thickness: Quantity,
    channel_depth: Optional,
):
    """Creates a new ChannelDimension instance."""

    return ChannelDimensions(
        flange_width=flange_width,
        flange_thickness=flange_thickness,
        web_thickness=web_thickness,
        depth=channel_depth,
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

    # @cached_property
    # def minor_axis_inertia(self):
    #     return (
    #         2 * self.flange_self_inertia_minor_axis
    #         + self.web_self_inertia_minor_axis
    #     )

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
            self.major_axis_inertia, self.dimensions.depth / 2
        )

    # @cached_property
    # def minor_axis_elastic_section_modulus(self):
    #     return section_modulus(
    #         self.minor_axis_inertia, self.dimensions.flange_width / 2
    #     )

    @cached_property
    def major_axis_radius_of_gyration(self):
        return radius_of_gyration(
            moment_of_inertia=self.major_axis_inertia,
            gross_section_area=self.area,
        )

    # @cached_property
    # def minor_axis_radius_of_gyration(self):
    #     return radius_of_gyration(
    #         moment_of_inertia=self.minor_axis_inertia,
    #         gross_section_area=self.area,
    #     )

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

    # @cached_property
    # def minor_axis_plastic_half_centroid(self):
    #     return areas_centroid(
    #         (
    #             (self.flange_area, self.dimensions.flange_width / 4),
    #             (self.web_area / 2, self.dimensions.web_thickness / 4),
    #         )
    #     )
    #
    # @cached_property
    # def minor_axis_plastic_half_area(self):
    #     return self.flange_area + self.web_area / 2
    #
    # @cached_property
    # def minor_axis_plastic_section_modulus(self):
    #     return (
    #         2
    #         * self.minor_axis_plastic_half_area
    #         * self.minor_axis_plastic_half_centroid
    #     )


def _partial_area_prop_dsi_channel(
    base_area_prop: _DoublySymmetricIandChannelBaseAreaProperties,
):
    return partial(
        AreaProperties,
        area=base_area_prop.area,
        major_axis_inertia=base_area_prop.major_axis_inertia,
        # minor_axis_inertia=base_area_prop.minor_axis_inertia,
        major_axis_elastic_section_modulus=base_area_prop.major_axis_elastic_section_modulus,
        # minor_axis_elastic_section_modulus=base_area_prop.minor_axis_elastic_section_modulus,
        major_axis_plastic_section_modulus=base_area_prop.major_axis_plastic_section_modulus,
        # minor_axis_plastic_section_modulus=base_area_prop.minor_axis_plastic_section_modulus,
        major_axis_radius_of_gyration=base_area_prop.major_axis_radius_of_gyration,
        # minor_axis_radius_of_gyration=base_area_prop.minor_axis_radius_of_gyration,
    )


def channel_minor_axis_inertia(
    dimensions: ChannelDimensions,
) -> tuple[Quantity, Quantity]:
    web_area = dimensions.web_thickness * dimensions.web_height
    web_base_centroid = dimensions.web_thickness / 2
    flange_area = dimensions.flange_width * dimensions.flange_thickness
    flange_base_centroid = dimensions.flange_width / 2
    y_neutral_axis = (
        web_area * web_base_centroid + 2 * flange_area * flange_base_centroid
    ) / (web_area + 2 * flange_area)
    web_self_inertia = self_inertia(
        width=dimensions.web_height, height=dimensions.web_thickness
    )
    web_transfer_inertia = web_area * (y_neutral_axis - web_base_centroid) ** 2
    flange_self_inertia = self_inertia(
        width=dimensions.flange_thickness, height=dimensions.flange_width
    )
    flange_transfer_inertia = (
        flange_area * (y_neutral_axis - flange_base_centroid) ** 2
    )
    return (
        web_transfer_inertia
        + web_self_inertia
        + (flange_self_inertia + flange_transfer_inertia) * 2,
        y_neutral_axis,
    )


def channel_shear_center_delta(
    flange_width_corrected: Quantity,
    alpha: float,
    web_thickness: Quantity,
) -> Quantity:
    """TORSIONAL SECTION PROPERTIES OF STEEL SHAPES
    Canadian Institute of Steel Construction, 2002

    [13] (Galambos 1968, SSRC 1998).
    """
    return flange_width_corrected * alpha - web_thickness / 2


def channel_area_properties(dimensions: ChannelDimensions):
    base_area_prop = _DoublySymmetricIandChannelBaseAreaProperties(dimensions)
    (
        flange_width_corrected,
        web_height_corrected,
    ) = channel_corrected_dimensions(
        web_thickness=dimensions.web_thickness,
        web_height=dimensions.depth,
        flange_thickness=dimensions.flange_thickness,
        flange_width=dimensions.flange_width,
    )
    alpha_ = alpha(
        flange_thickness=dimensions.flange_thickness,
        flange_width_corrected=flange_width_corrected,
        web_thickness=dimensions.web_thickness,
        web_height=web_height_corrected,
    )
    torsional_constant = channel_torsional_constant(
        flange_thickness=dimensions.flange_thickness,
        flange_width_corrected=flange_width_corrected,
        web_thickness=dimensions.web_thickness,
        web_height_corrected=web_height_corrected,
    )
    warping_constant = channel_warping_constant(
        flange_thickness=dimensions.flange_thickness,
        flange_width_corrected=flange_width_corrected,
        web_thickness=dimensions.web_thickness,
        web_height_corrected=web_height_corrected,
        alpha=alpha_,
    )
    minor_axis_inertia, y_neutral_axis = channel_minor_axis_inertia(dimensions)
    major_axis_shear_centroid = 0 * m
    minor_axis_shear_centroid: Quantity = (
        channel_shear_center_delta(
            flange_width_corrected=flange_width_corrected,
            alpha=alpha_,
            web_thickness=dimensions.web_thickness,
        )
        + y_neutral_axis
    )
    minor_axis_plastic_section_modulus = (
        minor_axis_plastic_section_modulus_i_channel(
            area=base_area_prop.area,
            depth=dimensions.depth,
            web_height=dimensions.web_height,
            web_thickness=dimensions.web_thickness,
            flange_width=dimensions.flange_width,
            flange_thickness=dimensions.flange_thickness
        )
    )

    minor_axis_radius_of_gyration = radius_of_gyration(
        moment_of_inertia=minor_axis_inertia,
        gross_section_area=base_area_prop.area,
    )
    minor_axis_elastic_section_modulus = section_modulus(
        minor_axis_inertia, y_neutral_axis
    )
    return _partial_area_prop_dsi_channel(base_area_prop)(
        torsional_constant=torsional_constant,
        polar_radius_of_gyration=polar_radius_of_gyration(
            minor_axis_shear_centroid=minor_axis_shear_centroid,
            major_axis_shear_centroid=major_axis_shear_centroid,
            area=base_area_prop.area,
            major_axis_inertia=base_area_prop.major_axis_inertia,
            minor_axis_inertia=minor_axis_inertia,
        ),
        warping_constant=warping_constant,
        minor_axis_plastic_section_modulus=minor_axis_plastic_section_modulus,
        minor_axis_radius_of_gyration=minor_axis_radius_of_gyration,
        minor_axis_elastic_section_modulus=minor_axis_elastic_section_modulus,
        minor_axis_inertia=minor_axis_inertia,
        major_axis_shear_centroid=major_axis_shear_centroid,
        minor_axis_shear_centroid=minor_axis_shear_centroid,
    )


class SectionChecks(Protocol):
    material: IsotropicMaterial
    area_properties: AreaProperties

    @property
    @abstractmethod
    def aisc_360_10(self) -> AISC_360_10_Rule_Check:
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
            construction=self.construction,
        )


@dataclass(frozen=True)
class Channel:
    dimensions: ChannelDimensions
    material: IsotropicMaterial
    area_properties: AreaProperties
    construction: ConstructionType = ConstructionType.ROLLED

    @cached_property
    def aisc_360_10(self):
        return ChannelAISC36010(
            dimensions=self.dimensions,
            material=self.material,
            area_properties=self.area_properties,
            construction=self.construction,
        )


def doubly_symmetric_i_area_properties(dimensions: DoublySymmetricIDimensions):
    base_area_prop = _DoublySymmetricIandChannelBaseAreaProperties(dimensions)
    minor_axis_inertia = (
        2 * base_area_prop.flange_self_inertia_minor_axis
        + base_area_prop.web_self_inertia_minor_axis
    )
    minor_axis_elastic_section_modulus = section_modulus(
        minor_axis_inertia, base_area_prop.dimensions.flange_width / 2
    )
    minor_axis_plastic_half_centroid = areas_centroid(
        (
            (
                base_area_prop.flange_area,
                base_area_prop.dimensions.flange_width / 4,
            ),
            (
                base_area_prop.web_area / 2,
                base_area_prop.dimensions.web_thickness / 4,
            ),
        )
    )

    minor_axis_plastic_half_area = (
        base_area_prop.flange_area + base_area_prop.web_area / 2
    )
    minor_axis_plastic_section_modulus = (
        2 * minor_axis_plastic_half_area * minor_axis_plastic_half_centroid
    )

    major_axis_shear_centroid = Quantity(0, m)
    minor_axis_shear_centroid = Quantity(0, m)
    torsional_constant = doubly_symmetric_i_torsional_constant(
        flange_width=dimensions.flange_width,
        total_height=dimensions.depth,
        flange_thickness=dimensions.flange_thickness,
        web_thickness=dimensions.web_thickness,
    )
    warping_constant = doubly_symmetric_i_warping_constant(
        moment_of_inertia=minor_axis_inertia,
        distance_between_flanges_centroid=dimensions.distance_between_centroids,
    )
    return _partial_area_prop_dsi_channel(base_area_prop)(
        torsional_constant=torsional_constant,
        polar_radius_of_gyration=polar_radius_of_gyration(
            minor_axis_shear_centroid=minor_axis_shear_centroid,
            major_axis_shear_centroid=major_axis_shear_centroid,
            area=base_area_prop.area,
            major_axis_inertia=base_area_prop.major_axis_inertia,
            minor_axis_inertia=minor_axis_inertia,
        ),
        warping_constant=warping_constant,
        minor_axis_inertia=minor_axis_inertia,
        minor_axis_elastic_section_modulus=minor_axis_elastic_section_modulus,
        minor_axis_plastic_section_modulus=minor_axis_plastic_section_modulus,
        minor_axis_radius_of_gyration=radius_of_gyration(
            minor_axis_inertia, base_area_prop.area
        ),
        major_axis_shear_centroid=major_axis_shear_centroid,
        minor_axis_shear_centroid=minor_axis_shear_centroid,
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


def create_channel(
    dimensions: ChannelDimensions,
    material: IsotropicMaterial,
    area_properties: AreaProperties = None,
    construction: ConstructionType = ConstructionType.ROLLED,
) -> Channel:
    return Channel(
        dimensions=dimensions,
        material=material,
        area_properties=area_properties or channel_area_properties(dimensions),
        construction=construction,
    )


def doubly_symmetric_i_torsional_constant(
    flange_width: Quantity,
    total_height: Quantity,
    flange_thickness: Quantity,
    web_thickness: Quantity,
) -> Quantity:
    return (
        2 * flange_width * flange_thickness**3
        + (total_height - flange_thickness) * web_thickness**3
    ) / 3


def web_height_from_total(
    depth: Quantity, flange_thickness: Quantity
) -> Quantity:
    return depth - 2 * flange_thickness


def _total_height(
    web_height: Quantity, flange_thickness: Quantity
) -> Quantity:
    return web_height + 2 * flange_thickness


def _channel_area(
    web_height: Quantity,
    web_thickness: Quantity,
    flange_width: Quantity,
    flange_thickness: Quantity,
):
    return web_height * web_thickness + 2 * flange_thickness * flange_width


def factor_h(
    major_axis_shear_centroid: Quantity,
    minor_axis_shear_centroid: Quantity,
    polar_radius_of_gyration: Quantity,
) -> float:
    """E4-10"""

    return 1 - ratio_simplify(
        (major_axis_shear_centroid**2 + minor_axis_shear_centroid**2),
        polar_radius_of_gyration,
    )
