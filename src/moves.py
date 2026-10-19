import random
from .model import Package, Truck, Placement, State, Orientation
from .geometry import dimensions, is_valid_placement

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

    # random decision devided by swap, move, rotate
    move = random.choice(["swap", "move", "rotate"])

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