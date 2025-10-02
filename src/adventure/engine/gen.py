from adventure.engine.world import World, Room, Item, Exit, DIRECTIONS
import random
from collections import deque

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

    # Create rooms with flavor
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

    start = ids[0]

    # Create 2 keys with tags that match their printed number (1-based)
    keys = []
    for number in (1, 2):
        key_tag = f"key:brass{number}"
        key_item = Item(name=f"brass key {number}", tags=[key_tag, "key"], description="A small brass key.")
        keys.append((key_tag, key_item))

    # Place keys in early rooms (rough heuristic)
    early = ids[: max(3, n_rooms // 3)]
    for _, item in keys:
        rooms[rng.choice(early)].items.append(item)

    # Lock two exits and assign key tags
    locked_assigned = 0
    for rid in ids:
        if locked_assigned >= 2:
            break
        for d, ex in list(rooms[rid].exits.items()):
            if locked_assigned >= 2:
                break
            if not ex.locked:
                tag, _ = keys[locked_assigned]
                ex.locked = True
                ex.key_tag = tag
                # Also lock reverse, if present
                rev = _reverse_exit(rooms, rid, d)
                if rev:
                    rev.locked = True
                    rev.key_tag = tag
                locked_assigned += 1

    world = World(rooms=rooms, start=start, seed=rng.randint(0, 1_000_000))

    # Ensure solvability
    _ensure_solvable(world)

    return world


def _connect(a, b, rng):
    da = _pick_dir(a, rng)
    db = _opp_dir(da)
    if da is None:
        return
    if db is None:
        db = _pick_dir(b, rng) or "south"
    a.exits[da] = Exit(to=b.id)
    b.exits[db] = Exit(to=a.id)


def _pick_dir(room, rng):
    cand = [d for d in DIRECTIONS if d not in room.exits]
    return rng.choice(cand) if cand else None


def _opp_dir(d):
    opp = {"north": "south", "south": "north", "east": "west", "west": "east", "up": "down", "down": "up"}
    return opp.get(d)


def _reverse_exit(rooms, rid_from, dir_from):
    room = rooms[rid_from]
    ex = room.exits[dir_from]
    other = rooms[ex.to]
    for d, e in other.exits.items():
        if e.to == rid_from:
            return e
    return None


def _reachable_without_locks(world: World):
    """Rooms reachable from start if locked exits are treated as walls."""
    from collections import deque
    seen = set([world.start])
    q = deque([world.start])
    while q:
        rid = q.popleft()
        room = world.rooms[rid]
        for d, ex in room.exits.items():
            if ex.locked:
                continue
            nid = ex.to
            if nid not in seen:
                seen.add(nid)
                q.append(nid)
    return seen


def _key_locations(world: World):
    """Map key_tag -> (room_id, item_ref)."""
    loc = {}
    for rid, room in world.rooms.items():
        for it in room.items:
            for t in it.tags:
                if t.startswith("key:"):
                    loc[t] = (rid, it)
    return loc


def _locked_key_tags(world: World):
    tags = set()
    for room in world.rooms.values():
        for ex in room.exits.values():
            if ex.locked and ex.key_tag:
                tags.add(ex.key_tag)
    return tags


def _unlock_one_exit_in_start_if_needed(world: World):
    start_room = world.rooms[world.start]
    if any(not ex.locked for ex in start_room.exits.values()):
        return
    # Unlock one exit and its reverse so the player can leave
    d, ex = next(iter(start_room.exits.items()))
    ex.locked = False
    rev = _reverse_exit(world.rooms, world.start, d)
    if rev:
        rev.locked = False


def _ensure_solvable(world: World):
    """
    Guarantees:
    - Start room has at least one unlocked exit.
    - Every locked exit's key is reachable without crossing locked exits.
    - If the start room has locked exits, ensure their keys are in the start room.
    """
    _unlock_one_exit_in_start_if_needed(world)

    reachable = _reachable_without_locks(world)
    key_loc = _key_locations(world)
    needed_tags = _locked_key_tags(world)

    # Move any unreachable needed keys into the start room
    for tag in needed_tags:
        if tag not in key_loc:
            continue
        rid, item = key_loc[tag]
        if rid not in reachable:
            try:
                world.rooms[rid].items.remove(item)
            except ValueError:
                pass
            world.rooms[world.start].items.append(item)

    # Extra safety: keys for locks *in the start room* must be in start
    start_room = world.rooms[world.start]
    start_lock_tags = {ex.key_tag for ex in start_room.exits.values() if ex.locked and ex.key_tag}
    key_loc = _key_locations(world)  # refresh
    for tag in start_lock_tags:
        if tag not in key_loc:
            # create it if missing (shouldn't happen)
            number = tag.replace("key:brass", "")
            item = Item(name=f"brass key {number}", tags=[tag, "key"], description="A small brass key.")
            world.rooms[world.start].items.append(item)
        else:
            rid, item = key_loc[tag]
            if rid != world.start:
                try:
                    world.rooms[rid].items.remove(item)
                except ValueError:
                    pass
                world.rooms[world.start].items.append(item)

