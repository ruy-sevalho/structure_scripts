from quantities import Quantity


def _representative_elastic_local_buckling_strength(
        elastic_critical_buckling_coefficient,
        modulus: Quantity,
        outside_diameter: Quantity,
        wall_thickness: Quantity
) -> Quantity:
    return 2 * elastic_critical_buckling_coefficient * modulus * wall_thickness / outside_diameter


def _local_buckling_strength(
        yield_strength: Quantity,
        representative_elastic_local_buckling_strength: Quantity,

):
    if yield_strength / representative_elastic_local_buckling_strength <= 0.17:
        strength = yield_strength
    else:
        strength = (
                (1.047 - 0.274 * yield_strength / representative_elastic_local_buckling_strength) * yield_strength
        )
    return strength
