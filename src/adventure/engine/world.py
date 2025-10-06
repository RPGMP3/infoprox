from dataclasses import dataclass, field
from typing import Dict, List, Optional

DIRECTIONS = ["north", "south", "east", "west", "up", "down"]

@dataclass
class Item:
    name: str
    tags: List[str] = field(default_factory=list)
    portable: bool = True
    description: str = ""

@dataclass
class Exit:
    to: str  # room id
    locked: bool = False
    key_tag: Optional[str] = None  # e.g., "key:rune1"
    description: str = ""

@dataclass
class Room:
    id: str
    name: str
    tags: List[str] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    exits: Dict[str, Exit] = field(default_factory=dict)
    seen: bool = False
    base_desc: str = ""

@dataclass
class World:
    rooms: Dict[str, Room]
    start: str
    seed: int
    theme: str  # "fantasy" | "scifi" | "horror"

def short_room_text(room: Room) -> str:
    exits = ", ".join([d for d in room.exits.keys()]) or "nowhere"
    seen = "You are in " if room.seen else "You arrive in "
    items = ""
    if room.items:
        names = ", ".join(i.name for i in room.items)
        items = f" You see {names}."
    return f"{seen}{room.name}. {room.base_desc} Exits lead {exits}.{items}"

