from src.geometry import dimensions, outOfBounds, overlaps, supports, volume
from src.model import Package, State, Truck


def score(truck: Truck, packages: dict[str, Package], state: State) -> float:
    # if not is_valid_placement(truck, packages, state):
    #     raise ValueError("State not valid")

    total_value = 0.0
    total_weight = 0
    placed_value = 0.0
    for package_id, placement in state.placements.items():
        if placement is None:
            continue

        package = packages[package_id]
        size = dimensions(package, placement.orientation)
        package_volume = volume(package)
        if package_volume != 0:
            value_per_cube = package.value / package_volume
        else:
            value_per_cube = 0

        total_value += package.value
        placed_value += package.value
        total_weight += package.weight

        # Calculate Penalties
        outofbounds_value = outOfBounds(placement, size, truck)
        overlap_value = 0
        support_value = 0
        fragile_value = 0
        for o_package_id, o_placement in state.placements.items():
            if o_placement is None or o_package_id == package_id:
                continue
            o_package = packages[o_package_id]
            o_size = dimensions(o_package, o_placement.orientation)

            overlap_value += overlaps(placement, size, o_placement, o_size)

            if placement.z != 0:
                support_value += supports(o_placement, o_size, placement, size)

            if placement.z != 0 and o_package.fragile:
                fragile_value += supports(o_placement, o_size, placement, size)

        # Apply penalties (weighted based on severity, can be configured)
        total_value -= outofbounds_value * value_per_cube * 1.1
        total_value -= overlap_value * value_per_cube * 1.1
        if placement.z != 0 and support_value <= 0:
            total_value -= package.value * 1.3
        if fragile_value >= 0:
            total_value -= fragile_value * size[2] * value_per_cube * 1.5 # times height since fragile_value is 2D surface of package

    if truck.max_capacity > 0 and total_weight > truck.max_capacity:
        # The more difference between total_weight and max_capacity, the more severe the penalty
        excess_weight = total_weight - truck.max_capacity
        total_value -= placed_value * (excess_weight / truck.max_capacity)

    return total_value


def package_count(truck: Truck, packages: dict[str, Package], state: State) -> int:
    count = 0
    for placement in state.placements.values():
        if placement is not None:
            count += 1

    return count
