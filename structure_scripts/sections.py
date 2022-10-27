from dataclasses import dataclass
from quantities import Quantity
from structure_scripts.helpers import radius_of_gyration


@dataclass(frozen=True)
class TwoAxisData:
    major_axis: Quantity
    minor_axis: Quantity


@dataclass(frozen=True)
class ThreeAxisData(TwoAxisData):
    torsion: Quantity


@dataclass(frozen=True)
class SectionGeoProperties:
    area: Quantity
    inertia: ThreeAxisData
    elastic_section_modulus: TwoAxisData
    plastic_section_modulus: TwoAxisData
    radius_of_gyration: ThreeAxisData
    warping_constant: Quantity


def section_geo_properties(
    area: Quantity,
    warping_constant: Quantity,
    major_axis_inertia: Quantity,
    major_axis_elastic_section_modulus: Quantity,
    minor_axis_inertia: Quantity,
    minor_axis_elastic_section_modulus: Quantity,
    polar_inertia: Quantity,
    major_axis_plastic_section_modulus: Quantity | None = None,
    minor_axis_plastic_section_modulus: Quantity | None = None,
    major_axis_radius_of_gyration: Quantity | None = None,
    minor_axis_radius_of_gyration: Quantity | None = None,
    torsional_radius_of_gyration: Quantity | None = None,
):
    return SectionGeoProperties(
        area=area,
        warping_constant=warping_constant,
        inertia=ThreeAxisData(
            major_axis=major_axis_inertia,
            minor_axis=minor_axis_inertia,
            torsion=polar_inertia,
        ),
        elastic_section_modulus=TwoAxisData(
            major_axis=major_axis_elastic_section_modulus,
            minor_axis=minor_axis_elastic_section_modulus,
        ),
        plastic_section_modulus=TwoAxisData(
            major_axis=major_axis_plastic_section_modulus
            or major_axis_elastic_section_modulus,
            minor_axis=minor_axis_plastic_section_modulus
            or minor_axis_elastic_section_modulus,
        ),
        radius_of_gyration=ThreeAxisData(
            major_axis=major_axis_radius_of_gyration
            or radius_of_gyration(
                moment_of_inertia=major_axis_inertia, gross_section_area=area
            ),
            minor_axis=minor_axis_radius_of_gyration
            or radius_of_gyration(
                moment_of_inertia=major_axis_inertia, gross_section_area=area
            ),
            torsion=torsional_radius_of_gyration
            or radius_of_gyration(
                moment_of_inertia=polar_inertia, gross_section_area=area
            ),
        ),
    )


#
# class AxisBending(Protocol):
#     @property
#     @abstractmethod
#     def inertia(self) -> Quantity:
#         pass
#
#     @property
#     @abstractmethod
#     def elastic_section_modulus(self) -> Quantity:
#         pass
#
#     @property
#     @abstractmethod
#     def plastic_section_modulus(self) -> Quantity:
#         pass
#
#     @property
#     @abstractmethod
#     def radius_of_gyration(self) -> Quantity:
#         pass
#
#
# @dataclass
# class AxisBendingData:
#     _inertia: Quantity
#     _elastic_section_modulus: Quantity
#     _plastic_section_modulus: Quantity
#     _radius_of_gyration: Quantity
#
#     @property
#     def inertia(self) -> Quantity:
#         return self._inertia
#
#     @property
#     def elastic_section_modulus(self) -> Quantity:
#         return self._elastic_section_modulus
#
#     @property
#     def plastic_section_modulus(self) -> Quantity:
#         return self._plastic_section_modulus
#
#     @property
#     def radius_of_gyration(self) -> Quantity:
#         return self._radius_of_gyration
#
#
# @runtime_checkable
# class Torsion(Protocol):
#     @property
#     @abstractmethod
#     def inertia(self) -> Quantity:
#         pass
#
#     @property
#     @abstractmethod
#     def radius_of_gyration(self) -> Quantity:
#         pass
#
#
# @dataclass(frozen=True)
# class TorsionData(Torsion):
#     _inertia: Quantity
#     _radius_of_gyration: Quantity
#
#     @property
#     def inertia(self) -> Quantity:
#         return self._inertia
#
#     @property
#     def radius_of_gyration(self) -> Quantity:
#         return self._radius_of_gyration
#
#
# class AreaProperties(Protocol):
#     @property
#     @abstractmethod
#     def area(self) -> Quantity:
#         pass
#
#     @property
#     @abstractmethod
#     def major_axis(self) -> AxisBending:
#         pass
#
#     @property
#     @abstractmethod
#     def minor_axis(self) -> AxisBending:
#         pass
#
#     @property
#     @abstractmethod
#     def torsion(self) -> Torsion:
#         pass
#
#     @property
#     @abstractmethod
#     def warping_constant(self) -> Quantity:
#         pass
#
#
# @dataclass(frozen=True)
# class DirectInputAreaProperties:
#     area: Quantity
#     major_axis_inertia: Quantity
#     major_axis_elastic_section_modulus: Quantity
#     minor_axis_inertia: Quantity
#     minor_axis_elastic_section_modulus: Quantity
#     polar_inertia: Quantity
#     major_axis_plastic_section_modulus: Quantity | None = None
#     minor_axis_plastic_section_modulus: Quantity | None = None
#     major_axis_radius_of_gyration: Quantity | None = None
#     minor_axis_radius_of_gyration: Quantity | None = None
#     torsional_radius_of_gyration: Quantity | None = None
#     warping_constant: Quantity | None = None
#
#     @property
#     def major_axis(self):
#         return AxisBendingData(
#             _inertia=self.major_axis_inertia,
#             _elastic_section_modulus=self.major_axis_elastic_section_modulus,
#             _plastic_section_modulus=self.major_axis_plastic_section_modulus
#             or self.major_axis_elastic_section_modulus,
#             _radius_of_gyration=self.major_axis_radius_of_gyration
#             or radius_of_gyration(self.major_axis_inertia, self.area),
#         )
#
#     @property
#     def minor_axis(self):
#         return AxisBendingData(
#             _inertia=self.minor_axis_inertia,
#             _elastic_section_modulus=self.minor_axis_elastic_section_modulus,
#             _plastic_section_modulus=self.minor_axis_plastic_section_modulus
#             or self.minor_axis_elastic_section_modulus,
#             _radius_of_gyration=self.minor_axis_radius_of_gyration
#             or radius_of_gyration(self.minor_axis_inertia, self.area),
#         )
#
#     @property
#     def torsion(self):
#         return TorsionData(
#             _inertia=self.polar_inertia,
#             _radius_of_gyration=self.torsional_radius_of_gyration
#             or radius_of_gyration(self.polar_inertia, self.area),
#         )
#
#
# def f(a: AreaProperties):
#     pass
#
#
# d = DirectInputAreaProperties()
# x = f(d)
