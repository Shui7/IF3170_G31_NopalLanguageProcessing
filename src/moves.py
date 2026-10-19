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