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

# check overlaps (if x, y, z of package A is in the range of package B)
def overlaps(a: Placement, a_size: tuple[int, int, int], b: Placement, b_size: tuple[int, int, int]) -> bool:
    a_x1, a_y1, a_z1 = a.x, a.y, a.z
    a_x2, a_y2, a_z2 = a.x + a_size[0], a.y + a_size[1], a.z + a_size[2]

    b_x1, b_y1, b_z1 = b.x, b.y, b.z
    b_x2, b_y2, b_z2 = b.x + b_size[0], b.y + b_size[1], b.z + b_size[2]

    return not (a_x2 <= b_x1 or a_x1 >= b_x2 or a_y2 <= b_y1 or a_y1 >= b_y2 or a_z2 <= b_z1 or a_z1 >= b_z2)

# check if package stacked on top of each other (if x, y of package A is in the range of package B)
def supports(a: Placement, a_size: tuple[int, int, int], b: Placement, b_size: tuple[int, int, int]) -> bool:
    a_x1, a_y1 = a.x, a.y
    a_x2, a_y2 = a.x + a_size[0], a.y + a_size[1]

    b_x1, b_y1 = b.x, b.y
    b_x2, b_y2 = b.x + b_size[0], b.y + b_size[1]

    return (a.z + a_size[2] == b.z and not (a_x2 < b_x1 or a_x1 > b_x2 or a_y2 < b_y1 or a_y1 > b_y2))

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

def score(truck: Truck, packages: dict[str, Package], state: State) -> int:
    if not is_valid_placement(truck, packages, state):
        raise ValueError("State not valid")

    total_value = 0
    for package_id, placement in state.placements.items():
        if placement is None:
            continue

        package = packages[package_id]
        total_value += package.value

    return total_value