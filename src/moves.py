import random
from .model import Package, Truck, Placement, State, Orientation

def generateRandomState(truck: Truck, packages: dict[str, Package]) -> State:
    placements: dict[str, Placement | None] = {}

    for package_id in packages:
        if random.random() < 0.2:
            placements[package_id] = None
            continue

        placements[package_id] = Placement(
            x=random.randint(0, truck.width - 1),
            y=random.randint(0, truck.length - 1),
            z=random.randint(0, truck.height - 1),
            orientation=random.choice(list(Orientation)),
        )

    return State(placements=placements)