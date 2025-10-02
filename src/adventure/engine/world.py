from dataclasses import dataclass, field
from typing import Dict, List, Optional

DIRECTIONS = ["north", "south", "east", "west", "up", "down"]


@dataclass
class Item:
    name: str
    tags: List[str] = field(default_factory=list)
    portable: bool = True
    description: str = ""
    weight: int = 1  # used for pressure plates


@dataclass
class Exit:
    to: str                  # room id
    locked: bool = False
    key_tag: Optional[str] = None  # e.g., "key:brass"
    description: str = ""
    requires_plate: bool = False   # gate that opens only while plate pressed


@dataclass
class Room:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    exits: Dict[str, Exit] = field(default_factory=dict)
    seen: bool = False
    base_desc: str = ""
    plate_threshold: Optional[int] = None  # total item weight needed to hold a plate down


@dataclass
class World:
    rooms: Dict[str, Room]
    start: str
    seed: int


def short_room_text(room: Room) -> str:
    exits = ", ".join([d for d in room.exits.keys()]) or "nowhere"
    seen = "You are in " if room.seen else "You arrive in "
    items = ""
    if room.items:
        names = ", ".join(i.name for i in room.items)
        items = f" You see {names}."
    plate = ""
    if room.plate_threshold is not None:
        plate = " A heavy stone plate rests in the floor."
    return f"{seen}{room.name}. {room.base_desc}{plate} Exits lead {exits}.{items}"

