import random
from struct import pack
from .model import Package, Truck, Placement, State, Orientation
from .geometry import dimensions, is_valid_placement
from itertools import combinations

def generateRandomState(truck: Truck, packages: dict[str, Package]) -> State:
    placements: dict[str, Placement | None] = {
        package_id: None for package_id in packages
    }

    package_ids = list(packages.keys())
    random.shuffle(package_ids)

    for package_id in package_ids:
        package = packages[package_id]
        if random.random() < 0.2:
            continue

        for _ in range(100):
            orientation = random.choice(list(Orientation))
            width, length, height = dimensions(package, orientation)
            if width > truck.width or length > truck.length or height > truck.height:
                continue
                
            possible_z = {0}
            for other_id, other in placements.items():
                if other is None:
                    continue
                other_h = dimensions(packages[other_id], other.orientation)[2]
                top_z = other.z + other_h
                if top_z + height <= truck.height:
                    possible_z.add(top_z)
            
            placement = Placement(
                x=random.randint(0, truck.width - width),
                y=random.randint(0, truck.length - length),
                z=random.choice(list(possible_z)),
                orientation=orientation,
            )

            candidate = placements.copy()
            candidate[package_id] = placement
    
            if is_valid_placement(truck, packages, State(candidate)):
                placements[package_id] = placement
                break

    return State(placements=placements)

def generate_neighbor(truck: Truck, packages: dict[str, Package], state: State):
    # create copy of current state
    placements = state.placements.copy()

    # get all current packages available
    package_ids = list(placements.keys())

    if not package_ids:
        return State(placements)

    move_types = ["swap", "move", "rotate"] if len(package_ids) >= 2 else ["move", "rotate"]
    move = random.choice(move_types)

    # swap two packages
    # by swapping its coordinates and orientation
    if move == "swap":
        # pick 2 random packages
        first_package_id, second_package_id = random.sample(package_ids, 2)
        first = placements[first_package_id]
        second = placements[second_package_id]

        # configure its orientation (if its outside truck pick default WLH)
        first_orientation = Orientation.WLH
        second_orientation = Orientation.WLH
        if first is not None:
            first_orientation = first.orientation
        if second is not None:
            second_orientation = second.orientation

        # temp clear both packages placement
        placements[first_package_id] = None
        placements[second_package_id] = None

        #swap both packages placement
        if first is not None:
            placements[second_package_id] = Placement(first.x, first.y, first.z, first_orientation)
        if second is not None:
            placements[first_package_id] = Placement(second.x, second.y, second.z, second_orientation)        

        return State(placements)

    # move packages
    # this includes insert/ditch in and out of truck
    if move == "move":
        # pick 1 random package
        package_id = random.choice(package_ids)
        old_placement = placements[package_id]


        # if package is outside of the truck, insert it into the truck with random coordinates and orientation
        if old_placement is None:
            # pick random coordinates and orientation
            # (coordinates will be set in branch fallback here)
            orientation = random.choice(list(Orientation))

        # if package is inside the truck, ditch it with 
        else:  
            remove_package = random.choice([True, False])
        
            if remove_package:
                placements[package_id] = None
                return State(placements)
        
            orientation = old_placement.orientation
    
        package = packages[package_id]
        width, length, height = dimensions(package, orientation)


        if width > truck.width or length > truck.length or height > truck.height:
            return State(placements)
        
        # generate random coordinates
        x = random.randint(0, truck.width - width)
        y = random.randint(0, truck.length - length)
        z = random.randint(0, truck.height - height)

        placements[package_id] = Placement(x, y, z, orientation)
        return State(placements)

    # rotate packages
    if move == "rotate":
        # pick 1 random package
        package_id = random.choice(package_ids)
        old_placement = placements[package_id]


        if old_placement is None:
            return State(placements)
        
        # rotate x y z at random orientation
        axes = list(old_placement.orientation.value)
        axis = random.choice(["x", "y", "z"])

        if axis == "x":
            axes[1], axes[2] = axes[2], axes[1]
        elif axis == "y":
            axes[0], axes[2] = axes[2], axes[0] 
        else: # axis == "z":
            axes[0], axes[1] = axes[1], axes[0]

        orientation = Orientation(tuple(axes))

        placements[package_id] = Placement(old_placement.x, old_placement.y, old_placement.z, orientation)

        return State(placements)

    return State(placements={})

def replace_package(state: State, package_id: str, placement: Placement | None) -> State:
    placements = state.placements.copy()
    placements[package_id] = placement
    return State(placements=placements)

def move_package(state: State, package_id: str, new_placement: Placement | None) -> State:
    return replace_package(state, package_id, new_placement)

def swap_packages(state: State, a_id: str, b_id: str) -> State:
    if a_id == b_id:
        return state

    a = state.placements[a_id]
    b = state.placements[b_id]
    placements = state.placements.copy()

    if a is not None and b is not None:
        placements[a_id] = Placement(b.x, b.y, b.z, a.orientation)
        placements[b_id] = Placement(a.x, a.y, a.z, b.orientation)
    else:
        placements[a_id] = b
        placements[b_id] = a

    return State(placements=placements)

def rotate_package(state: State, package_id: str, axis: str) -> State:
    if axis not in ("x", "y", "z"):
        return state

    old_placement = state.placements[package_id]
    if old_placement is None:
        return state

    indices = {
        "x": (1, 2),
        "y": (0, 2),
        "z": (0, 1)
    }
    i, j = indices[axis]
    orient = list(old_placement.orientation.value)
    orient[i], orient[j] = orient[j], orient[i]
    return replace_package(state, package_id, Placement(old_placement.x, old_placement.y, old_placement.z, Orientation(tuple(orient))))

def add_neighbor(truck: Truck, packages: dict[str, Package], candidate: State, package_ids: list[str], seen: set[tuple[Placement | None, ...]], neighbors: list[State]) -> None:
    key = tuple(candidate.placements[pid] for pid in package_ids)
    if key not in seen and is_valid_placement(truck, packages, candidate):
        seen.add(key)
        neighbors.append(candidate)

def generate_neighbors(truck: Truck, packages: dict[str, Package], state: State) -> list[State]:
    neighbors: list[State] = []
    package_ids = list(state.placements)
    seen = {tuple(state.placements[pid] for pid in package_ids)}

    for a_id, b_id in combinations(package_ids, 2):
        add_neighbor(truck, packages, swap_packages(state, a_id, b_id), package_ids, seen, neighbors)

    for package_id, current in state.placements.items():
        if current is not None:
            add_neighbor(truck, packages, move_package(state, package_id, None), package_ids, seen, neighbors)
            for axis in ("x", "y", "z"):
                add_neighbor(truck, packages, rotate_package(state, package_id, axis), package_ids, seen, neighbors)

        package = packages[package_id]
        orientations = list(Orientation) if current is None else [current.orientation]
        for orientation in orientations:
            width, length, height = dimensions(package, orientation)
            if width > truck.width or length > truck.length or height > truck.height:
                continue

            possible_z = {0}
            for other_id, other in state.placements.items():
                if other_id == package_id or other is None or packages[other_id].fragile:
                    continue
                other_height = dimensions(packages[other_id], other.orientation)[2]
                top_z = other.z + other_height
                if top_z + height <= truck.height:
                    possible_z.add(top_z)

            for x in range(truck.width - width + 1):
                for y in range(truck.length - length + 1):
                    for z in sorted(possible_z):
                        placement = Placement(x, y, z, orientation)
                        add_neighbor(truck, packages, move_package(state, package_id, placement), package_ids, seen, neighbors)
    return neighbors