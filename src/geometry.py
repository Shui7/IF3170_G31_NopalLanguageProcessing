from .model import Package, Truck, Placement, State, Orientation

# check dimensions
def dimensions(package: Package, orientation: Orientation) -> tuple[int, int, int]:
    if orientation == Orientation.WLH:
        return package.width, package.length, package.height
    elif orientation == Orientation.WHL:
        return package.width, package.height, package.length
    elif orientation == Orientation.LWH:
        return package.length, package.width, package.height
    elif orientation == Orientation.LHW:
        return package.length, package.height, package.width
    elif orientation == Orientation.HWL:
        return package.height, package.width, package.length
    elif orientation == Orientation.HLW:
        return package.height, package.length, package.width
    else:
        raise ValueError(f"Invalid orientation: {orientation}")

def volume(package: Package):
    return package.length * package.width * package.height

# Return the number of unit cubes that overlaps between two packages.
def overlaps(a: Placement, a_size: tuple[int, int, int], b: Placement, b_size: tuple[int, int, int]) -> int:
    a_x1, a_y1, a_z1 = a.x, a.y, a.z
    a_x2, a_y2, a_z2 = a.x + a_size[0], a.y + a_size[1], a.z + a_size[2]

    b_x1, b_y1, b_z1 = b.x, b.y, b.z
    b_x2, b_y2, b_z2 = b.x + b_size[0], b.y + b_size[1], b.z + b_size[2]

    overlap_width = max(0, min(a_x2, b_x2) - max(a_x1, b_x1))
    overlap_length = max(0, min(a_y2, b_y2) - max(a_y1, b_y1))
    overlap_height = max(0, min(a_z2, b_z2) - max(a_z1, b_z1))

    return overlap_width * overlap_length * overlap_height

# Returns support area, with first package below second package.
def supports(a: Placement, a_size: tuple[int, int, int], b: Placement, b_size: tuple[int, int, int]) -> int:
    a_x1, a_y1 = a.x, a.y
    a_x2, a_y2 = a.x + a_size[0], a.y + a_size[1]

    b_x1, b_y1 = b.x, b.y
    b_x2, b_y2 = b.x + b_size[0], b.y + b_size[1]

    if a.z + a_size[2] != b.z:
        return 0

    contact_width = max(0, min(a_x2, b_x2) - max(a_x1, b_x1))
    contact_length = max(0, min(a_y2, b_y2) - max(a_y1, b_y1))

    return contact_width * contact_length

# Returns package volume that is outside the truck
def outOfBounds(a: Placement, a_size: tuple[int, int, int], truck: Truck) -> int:
    package_volume = a_size[0] * a_size[1] * a_size[2]

    inside_width = max(0, min(a.x + a_size[0], truck.width) - a.x)
    inside_length = max(0, min(a.y + a_size[1], truck.length) - a.y)
    inside_height = max(0, min(a.z + a_size[2], truck.height) - a.z)

    inside_volume = inside_width * inside_length * inside_height
    return package_volume - inside_volume

def is_valid_placement(truck: Truck, packages: dict[str, Package], state: State) -> bool:
    if set(state.placements) != set(packages):
        return False

    # package, placement, dimeonsions
    placed_packages = []
    total_weight = 0

    for package_id, placement in state.placements.items():
        if placement is None:
            continue

        package = packages[package_id]
        size = dimensions(package, placement.orientation)
        w, l, h = size

        # valdiation check if its withn range
        if (min(placement.x, placement.y, placement.z) < 0 or
                placement.x + w > truck.width or
                placement.y + l > truck.length or
                placement.z + h > truck.height):
            return False

        total_weight += package.weight
        placed_packages.append((package, placement, size))

    if total_weight > truck.max_capacity:
        return False

    # check if overlaps
    for i, (_, a, a_size) in enumerate(placed_packages):
        for _, b, b_size in placed_packages[i + 1:]:
            if overlaps(a, a_size, b, b_size):
                return False

    # check if supports
    for _, upper, upper_size in placed_packages:
        # check if in the truck floor
        if upper.z == 0:
            continue

        supporting_packages = []
        for lower_package, lower, lower_size in placed_packages:
            # ignore if package is the same
            if lower is upper:
                continue
            
            #check if lower package is below the upper package
            if supports(lower, lower_size, upper, upper_size):
                supporting_packages.append(lower_package)

        if not supporting_packages:
            return False

        for package in supporting_packages:
            if package.fragile:
                return False
            
    return True

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
            total_value -= fragile_value * size[2] * package.value * 1.5 # times height since fragile_value is 2D surface of package

    if truck.max_capacity > 0 and total_weight > truck.max_capacity:
        # The more difference between total_weight and max_capacity, the more severe the penalty
        excess_weight = total_weight - truck.max_capacity
        total_value -= placed_value * (excess_weight / truck.max_capacity)

    return total_value