from dataclasses import dataclass
from enum import Enum

# Package:
# id
# Dimensions (represented as width, length, height)
# Orientation (represented as width, length, height)
# Value
# Weight
# IsFragile
# ETA
@dataclass(frozen=True)
class Package:
    id: str
    width: int
    length: int
    height: int
    value: int
    weight: int
    fragile: bool
    eta: int

# Truck:
# Dimensions (represented as width, length, height)
# MaxCapacity 
@dataclass(frozen=True)
class Truck:
    width: int
    length: int
    height: int
    max_capacity: int

# Orientation represented as x, y, z
# x = width, y = length, z = height
class Orientation(Enum):
    WLH = ("w", "l", "h")
    WHL = ("w", "h", "l")
    LWH = ("l", "w", "h")
    LHW = ("l", "h", "w")
    HWL = ("h", "w", "l")
    HLW = ("h", "l", "w")

@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    z: int
    orientation: Orientation

# State value
# key: Package.id, value: Placement
# kalau None berarti package belum ditempatkan di truck
@dataclass(frozen=True)
class State:
    placements: dict[str, Placement | None]