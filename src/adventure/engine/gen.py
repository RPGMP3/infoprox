from adventure.engine.world import World, Room, Item, Exit, DIRECTIONS
import random

ROOM_NAMES = [
    ("atrium", ["airy", "echoing"]),
    ("archives", ["dusty", "silent"]),
    ("laboratory", ["sterile", "cluttered"]),
    ("vault", ["cold", "secure"]),
    ("observatory", ["dim", "domed"]),
    ("workshop", ["greasy", "crowded"]),
]

def make_world(seed=None, n_rooms=10) -> World:
    rng = random.Random(seed)
    ids = [f"r{i}" for i in range(n_rooms)]
    rng.shuffle(ids)

    rooms = {}
    for rid in ids:
        name, adjs = rng.choice(ROOM_NAMES)
        adj = rng.choice(adjs)
        base_desc = f"A {adj} {name}."
        rooms[rid] = Room(id=rid, name=name.title(), tags=[name, adj], base_desc=base_desc)

    # Connect rooms as a chain, then add a few extra links
    for a, b in zip(ids, ids[1:]):
        _connect(rooms[a], rooms[b], rng)

    for _ in range(max(1, n_rooms // 3)):
        a, b = rng.sample(ids, 2)
        _connect(rooms[a], rooms[b], rng)

    # Place keys in early-accessible rooms
    keys = []
    for kix in range(2):
        key_tag = f"key:brass{kix}"
        key_item = Item(name=f"brass key {kix+1}", tags=[key_tag, "key"], description="A small brass key.")
        keys.append((key_tag, key_item))

    early = ids[: max(3, n_rooms // 3)]
    for _, item in keys:
        rid = rng.choice(early)
        rooms[rid].items.append(item)

    # Lock two random exits with those keys
    locked = 0
    for rid in ids:
        for d, ex in list(rooms[rid].exits.items()):
            if locked >= 2:
                break
            if not ex.locked:
                tag, _ = keys[locked]
                ex.locked = True
                ex.key_tag = tag
                locked += 1
                rev = _reverse_exit(rooms, rid, d)
                if rev:
                    rev.locked = True
                    rev.key_tag = tag
        if locked >= 2:
            break

    start = ids[0]
    return World(rooms=rooms, start=start, seed=rng.randint(0, 1_000_000))

def _connect(a: Room, b: Room, rng: random.Random) -> None:
    da = _pick_dir(a, rng)
    if da is None:
        return
    db = _opp_dir(da) or _pick_dir(b, rng) or "south"
    a.exits[da] = Exit(to=b.id)
    b.exits[db] = Exit(to=a.id)

def _pick_dir(room: Room, rng: random.Random):
    cand = [d for d in DIRECTIONS if d not in room.exits]
    return rng.choice(cand) if cand else None

def _opp_dir(d: str):
    opp = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}
    return opp.get(d)

def _reverse_exit(rooms: dict, rid_from: str, dir_from: str):
    room = rooms[rid_from]
    ex = room.exits[dir_from]
    other = rooms[ex.to]
    for d, e in other.exits.items():
        if e.to == rid_from:
            return e
    return None

