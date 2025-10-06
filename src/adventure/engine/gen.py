from adventure.engine.world import World, Room, Item, Exit, DIRECTIONS
import random
from collections import deque

# We’ll keep most links horizontal (N/S/E/W) and add at most a couple vertical links.
H_DIRS = ["north", "south", "east", "west"]

THEMES = {
    "fantasy": {
        "archetypes": [
            ("great_hall", "Great Hall", ["drafty", "echoing"]),
            ("archives", "Archives", ["dusty", "quiet"]),
            ("laboratory", "Laboratory", ["cluttered", "alchemical"]),
            ("vault", "Sanctum", ["cold", "warded"]),
            ("observatory", "Observatory", ["domed", "dim"]),
            ("workshop", "Workshop", ["crowded", "greasy"]),
            ("catacombs", "Catacombs", ["stale", "narrow"]),
            ("garden", "Hanging Garden", ["overgrown", "ivy-choked"]),
            ("chapel", "Chapel", ["silent", "hushed"]),
            ("library", "Library", ["ink-stained", "stacked"]),
        ],
        "key_prefix": "key:rune",
        "key_display": lambda n: f"rune key {n}",
        "note_name": "weathered scroll",
        "note_line": lambda d: f"A cramped script: 'The rune key turns the {d or 'far'} door.'",
        "vault_arch": "vault",
        "vault_fixture": Item(
            name="ancient altar",
            tags=["fixture", "altar"],
            portable=False,
            description="An altar of old stone, waiting for three relics."
        ),
        "artifact_names": ["sun shard", "moon seal", "prism of whispers"],
    },
    "scifi": {
        "archetypes": [
            ("cryo_lab", "Cryo Lab", ["frosted", "sealed"]),
            ("server_room", "Server Room", ["humming", "cold"]),
            ("reactor_core", "Reactor Core", ["ringing", "shielded"]),
            ("observation_deck", "Observation Deck", ["broad", "star-lit"]),
            ("cargo_bay", "Cargo Bay", ["pressurized", "spacious"]),
            ("medbay", "Medbay", ["sterile", "bright"]),
            ("maintenance", "Maintenance", ["grimy", "tight"]),
            ("command", "Command", ["quiet", "lit"]),
            ("airlock", "Airlock", ["striped", "sealed"]),
            ("drone_hangar", "Drone Hangar", ["vacant", "oily"]),
            ("vault", "Core Chamber", ["armored", "secure"]),
        ],
        "key_prefix": "key:keycard",
        "key_display": lambda n: f"access keycard {n}",
        "note_name": "data-slate",
        "note_line": lambda d: f"System note: 'Keycard authorizes {d or 'restricted'} access.'",
        "vault_arch": "vault",
        "vault_fixture": Item(
            name="control pedestal",
            tags=["fixture", "console"],
            portable=False,
            description="A pedestal awaits three modules to complete the sequence."
        ),
        "artifact_names": ["quantum shard", "plasma coil", "nav chip"],
    },
    "horror": {
        "archetypes": [
            ("cellar", "Cellar", ["damp", "low"]),
            ("morgue", "Morgue", ["cold", "stale"]),
            ("ward", "Abandoned Ward", ["dim", "silent"]),
            ("chapel", "Chapel", ["tilted", "faded"]),
            ("attic", "Attic", ["tight", "dusty"]),
            ("boiler_room", "Boiler Room", ["hot", "clanging"]),
            ("ritual_chamber", "Ritual Chamber", ["scarred", "rank"]),
            ("nursery", "Nursery", ["still", "old"]),
            ("dining_room", "Dining Room", ["formal", "wrong"]),
            ("vault", "Sealed Cellar", ["bolted", "cold"]),
        ],
        "key_prefix": "key:rusted",
        "key_display": lambda n: f"rusted key {n}",
        "note_name": "bloodstained note",
        "note_line": lambda d: f"A smeared hand: 'The key fits the {d or 'other'} door.'",
        "vault_arch": "vault",
        "vault_fixture": Item(
            name="sealed threshold",
            tags=["fixture", "threshold"],
            portable=False,
            description="A threshold veined with sigils. Three mementos might quiet it."
        ),
        "artifact_names": ["cold locket", "torn photograph", "strange tooth"],
    },
}

def make_world(seed=None, n_rooms=12, theme="fantasy") -> World:
    theme = (theme or "fantasy").lower()
    if theme not in THEMES:
        theme = "fantasy"
    # Hard cap: keep things focused
    n_rooms = max(8, min(15, int(n_rooms or 12)))

    rng = random.Random(seed)
    ids = [f"r{i}" for i in range(n_rooms)]
    rng.shuffle(ids)

    T = THEMES[theme]
    archs = T["archetypes"]

    # Rooms with theme + archetype tags
    rooms = {}
    for rid in ids:
        arch_id, display, adjs = rng.choice(archs)
        adj = rng.choice(adjs)
        base_desc = f"A {adj} {display.lower()}."
        rooms[rid] = Room(
            id=rid,
            name=display,
            tags=[f"arch:{arch_id}", f"theme:{theme}", adj],
            base_desc=base_desc,
        )

    # --- Graph: a simple chain (spine) + a few extra horizontal links for mild branching ---
    # (horizontal only for clarity; we'll add <=2 vertical links later)
    for a, b in zip(ids, ids[1:]):
        _connect(rooms[a], rooms[b], rng, allowed_dirs=H_DIRS)

    extra_links = max(0, n_rooms // 6 - 1)  # softer branching than before
    for _ in range(extra_links):
        a, b = rng.sample(ids, 2)
        _connect(rooms[a], rooms[b], rng, allowed_dirs=H_DIRS)

    # Add at most 0–2 vertical links to keep levels sane
    v_links = 0
    if n_rooms >= 10:
        v_links = 1
    if n_rooms >= 14:
        v_links = 2
    _add_vertical_links(rooms, rng, v_links=v_links)

    start = ids[0]

    # Choose a Vault room (by arch tag); ensure at least one exit
    vault_id = None
    for rid, r in rooms.items():
        if f"arch:{T['vault_arch']}" in r.tags:
            vault_id = rid
            break
    if not vault_id:
        vault_id = ids[-1]
        rooms[vault_id].name = "Vault"
        if f"arch:{T['vault_arch']}" not in rooms[vault_id].tags:
            rooms[vault_id].tags.append(f"arch:{T['vault_arch']}")
        rooms[vault_id].base_desc = f"A {rng.choice(['cold', 'sealed'])} vault."

    if not rooms[vault_id].exits:
        other = rng.choice([i for i in ids if i != vault_id])
        _connect(rooms[vault_id], rooms[other], rng, allowed_dirs=H_DIRS)

    # Place a visible goal fixture in the vault (flavor, non-portable)
    rooms[vault_id].items.append(T["vault_fixture"])

    # Keys (1-based), theme display + tags "key:<prefix><n>"
    keys = []
    for number in (1, 2):
        key_tag = f"{T['key_prefix']}{number}"  # e.g., key:rune1 / key:keycard1 / key:rusted1
        key_item = Item(
            name=T["key_display"](number),
            tags=[key_tag, "key"],
            description="It fits something around here.",
        )
        keys.append((key_tag, key_item))

    # Place keys in early rooms
    early = ids[: max(3, n_rooms // 3)]
    for _, item in keys:
        rooms[random.choice(early)].items.append(item)

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
                # lock reverse
                rev = _reverse_exit(rooms, rid, d)
                if rev:
                    rev.locked = True
                    rev.key_tag = tag
                locked_assigned += 1

    # Add a theme note near each key
    for rid, room in rooms.items():
        for it in list(room.items):
            if any(t.startswith("key:") for t in it.tags):
                hint_dir = None
                for d, ex in room.exits.items():
                    if ex.locked:
                        hint_dir = d
                        break
                note = Item(
                    name=T["note_name"],
                    tags=["note", "paper"],
                    portable=True,
                    description=T["note_line"](hint_dir),
                )
                room.items.append(note)
                break

    # Lock one Vault exit with goal gate requiring 3 artifacts
    for d, ex in rooms[vault_id].exits.items():
        ex.locked = True
        ex.key_tag = "goal:artifacts3"
        rev = _reverse_exit(rooms, vault_id, d)
        if rev:
            rev.locked = True
            rev.key_tag = "goal:artifacts3"
        break

    # Place 3 artifacts (theme-specific) in non-vault rooms
    artifact_rooms = [rid for rid in ids if rid != vault_id]
    random.shuffle(artifact_rooms)
    for name, rid in zip(T["artifact_names"], artifact_rooms[:3]):
        rooms[rid].items.append(
            Item(
                name=name,
                tags=[f"artifact:{name.split()[0]}"],
                description=f"A curious {name}. It feels significant.",
            )
        )

    world = World(
        rooms=rooms,
        start=start,
        seed=random.randint(0, 1_000_000),
        theme=theme,
    )

    _ensure_solvable(world)
    return world


# ---------- connection helpers ----------

def _connect(a, b, rng, allowed_dirs=H_DIRS):
    da = _pick_dir(a, rng, allowed_dirs)
    db = _opp_dir(da)
    if da is None:
        return
    if db is None:
        # if opposite isn't available on target, try any allowed
        db = _pick_dir(b, rng, allowed_dirs) or "south"
    a.exits[da] = Exit(to=b.id)
    b.exits[db] = Exit(to=a.id)

def _connect_specific(a, b, dir_a, dir_b):
    """Try to connect a->b using specific directions, if both are free."""
    if dir_a in a.exits or dir_b in b.exits:
        return False
    a.exits[dir_a] = Exit(to=b.id)
    b.exits[dir_b] = Exit(to=a.id)
    return True

def _add_vertical_links(rooms, rng, v_links=1):
    # Try to add up to v_links vertical connections between random pairs
    if v_links <= 0:
        return
    ids = list(rooms.keys())
    tries = 0
    added = 0
    while added < v_links and tries < 100:
        tries += 1
        a_id, b_id = rng.sample(ids, 2)
        a, b = rooms[a_id], rooms[b_id]
        # connect with up/down if both free
        ok = _connect_specific(a, b, "up", "down")
        if ok:
            added += 1

def _pick_dir(room, rng, allowed_dirs):
    cand = [d for d in allowed_dirs if d not in room.exits]
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


# ---------- solvability helpers ----------

def _reachable_without_locks(world: World):
    """Rooms reachable from start if locked exits are walls."""
    seen = {world.start}
    q = deque([world.start])
    while q:
        rid = q.popleft()
        for ex in world.rooms[rid].exits.values():
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
    """Set of key tags used by locked exits (ignore goal gate)."""
    tags = set()
    for room in world.rooms.values():
        for ex in room.exits.values():
            if ex.locked and ex.key_tag and ex.key_tag.startswith("key:"):
                tags.add(ex.key_tag)
    return tags

def _unlock_one_exit_in_start_if_needed(world: World):
    """Ensure start room has at least one unlocked exit."""
    start_room = world.rooms[world.start]
    if any(not ex.locked for ex in start_room.exits.values()):
        return
    d, ex = next(iter(start_room.exits.items()))
    ex.locked = False
    rev = _reverse_exit(world.rooms, world.start, d)
    if rev:
        rev.locked = False

def _ensure_solvable(world: World):
    """
    - Start room has an unlocked exit.
    - Every key-locked exit's key is reachable without crossing locked exits.
    - Keys for any locked exits in start room are placed in start.
    """
    _unlock_one_exit_in_start_if_needed(world)

    reachable = _reachable_without_locks(world)
    key_loc = _key_locations(world)
    needed_tags = _locked_key_tags(world)

    # Move unreachable keys into start
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

    # Ensure keys for locks in start are in start
    start_room = world.rooms[world.start]
    start_lock_tags = {
        ex.key_tag
        for ex in start_room.exits.values()
        if ex.locked and ex.key_tag and ex.key_tag.startswith("key:")
    }
    key_loc = _key_locations(world)  # refresh
    for tag in start_lock_tags:
        if tag not in key_loc:
            # create it if missing (shouldn't happen)
            prefix = THEMES[world.theme]["key_prefix"]
            number = tag.split(prefix)[-1]
            item = Item(
                name=THEMES[world.theme]["key_display"](number),
                tags=[tag, "key"],
                description="It fits something around here.",
            )
            world.rooms[world.start].items.append(item)
        else:
            rid, item = key_loc[tag]
            if rid != world.start:
                try:
                    world.rooms[rid].items.remove(item)
                except ValueError:
                    pass
                world.rooms[world.start].items.append(item)

