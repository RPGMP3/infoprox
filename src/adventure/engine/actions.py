from adventure.engine.world import short_room_text
from adventure.engine.parser import DIR_SYNONYMS
from adventure.engine.describe import room_text
import re

# --- movement deltas for mapping ---
DIR_DELTAS = {
    "north": (0, -1, 0),
    "south": (0,  1, 0),
    "east":  (1,  0, 0),
    "west":  (-1, 0, 0),
    "up":    (0,  0, 1),
    "down":  (0,  0,-1),
}

def do_look(gs) -> str:
    room = gs.room
    room.seen = True
    text = room_text(room, seen=True)

    locked = [d for d, ex in room.exits.items() if ex.locked]
    extras = []
    if locked:
        extras.append("Locked: " + ", ".join(locked) + ".")
    if any(("note" in it.tags or "paper" in it.tags) for it in room.items):
        extras.append("There is a note here.")
    if extras:
        text += "\n" + " ".join(extras)
    return text


def do_go(gs, direction: str) -> str:
    room = gs.room
    ex = room.exits.get(direction)
    if not ex:
        return "You can't go that way."
    if ex.locked:
        return "It's locked."
    # record mapping BEFORE changing rooms
    _record_mapping(gs, direction, ex.to)
    gs.room = gs.world.rooms[ex.to]
    return do_look(gs)

def do_take(gs, item_name: str) -> str:
    if not item_name:
        return "Take what?"
    item = _find_item(gs.room.items, item_name)
    if not item:
        return "You don't see that here."
    if not item.portable:
        return "You can't take that."
    gs.room.items.remove(item)
    gs.inv.append(item)
    gs.score += 1
    return "Taken."

def do_inventory(gs) -> str:
    if not gs.inv:
        return "You are carrying nothing."
    names = ", ".join(i.name for i in gs.inv)
    return f"You are carrying: {names}."

def do_use(gs, item_name: str, target: str) -> str:
    """
    Use or unlock. Smart behavior:
    - If you have a matching key, `unlock`/`use` can unlock targeted dir (e.g., 'up') or any matching locks here.
    - Goal gate: if carrying 3 artifacts, `use` (no item) opens it.
    """
    exits = gs.room.exits

    # Normalize/derive direction from target or item_name (for "unlock up", "use up door")
    dir_target = _normalize_dir(target)
    if not dir_target:
        dir_target = _normalize_dir(item_name)

    def _artifact_count():
        return sum(1 for it in gs.inv if any(tag.startswith("artifact:") for tag in it.tags))

    # No item: try goal gate, then auto-unlock with any carried keys
    if not item_name:
        for d, ex in exits.items():
            if ex.locked and ex.key_tag == "goal:artifacts3":
                if _artifact_count() >= 3:
                    ex.locked = False
                    _unlock_reverse(gs, ex)
                    gs.score += 10
                    return "The artifacts resonate. The vault seals part with a deep click."
                else:
                    return "The way is sealed; something more is required."
        unlocked_dirs = _auto_unlock_with_inventory(gs, dir_target)
        if unlocked_dirs:
            gs.score += 5
            return _unlocked_msg(unlocked_dirs)
        return "Use what?"

    # Item provided: try to find it; if not, attempt auto-unlock anyway
    item = _find_item(gs.inv, item_name)
    if not item:
        unlocked_dirs = _auto_unlock_with_inventory(gs, dir_target)
        if unlocked_dirs:
            gs.score += 5
            return _unlocked_msg(unlocked_dirs)
        return "You don't have that."

    # Keys are tagged like key:*, e.g. key:rune1 / key:keycard1 / key:rusted1
    key_tags = [t for t in item.tags if t.startswith("key:")]

    if key_tags:
        pairs = []
        if dir_target:
            ex = exits.get(dir_target)
            if not ex:
                return "There's nothing like that here."
            pairs = [(dir_target, ex)]
        else:
            pairs = list(exits.items())

        unlocked_dirs = []
        for d, ex in pairs:
            if ex.locked and ex.key_tag in key_tags:
                ex.locked = False
                unlocked_dirs.append(d)
                _unlock_reverse(gs, ex)

        if unlocked_dirs:
            gs.score += 5
            return _unlocked_msg(unlocked_dirs)

    # Goal gate even if the item isn't a key
    for d, ex in exits.items():
        if ex.locked and ex.key_tag == "goal:artifacts3":
            if _artifact_count() >= 3:
                ex.locked = False
                _unlock_reverse(gs, ex)
                gs.score += 10
                return "The artifacts resonate. The vault seals part with a deep click."
            else:
                return "The way is sealed; something more is required."

    # Finally, try auto with any keys we hold
    unlocked_dirs = _auto_unlock_with_inventory(gs, dir_target)
    if unlocked_dirs:
        gs.score += 5
        return _unlocked_msg(unlocked_dirs)

    if any(ex.locked for ex in exits.values()):
        return "No matching locks here."
    return "Nothing happens."

def do_examine(gs, item_name: str) -> str:
    if not item_name:
        return "Examine what?"
    item = _find_item(gs.inv, item_name) or _find_item(gs.room.items, item_name)
    if not item:
        return "You don't see that."
    return item.description or f"It's {item.name.lower()}."

def do_read(gs, item_name: str) -> str:
    if not item_name:
        return "Read what?"
    item = _find_item(gs.inv, item_name) or _find_item(gs.room.items, item_name)
    if not item:
        return "You don't see that."
    if "note" in item.tags or "paper" in item.tags or "book" in item.tags:
        return item.description or "The writing has faded beyond use."
    return "There's nothing to read on that."

def do_map(gs, scope: str = "") -> str:
    """
    Draw an ASCII map of explored rooms with a legend:
      [@] = you, [o] = room, [^] = room with Up, [v] = room with Down, [*] = Up+Down
      '-' / '|' = open corridor (E/W or N/S)
      '=' / '!' = locked door (E/W or N/S)
      '>' = unexplored east exit (destination not mapped yet)
      ' . ' = unexplored south exit (destination not mapped yet)
    Note: West/North exits to unmapped rooms will show as east/south stubs once you reveal the adjacent space.
    Use `map` for current level, `map all` for all discovered Z-levels.
    """
    coords = getattr(gs, "map_coords", {})
    if not coords:
        return "No map yet."

    # Build layers: z -> {(x,y): room_id}
    layers = {}
    for rid, (x, y, z) in coords.items():
        layers.setdefault(z, {})[(x, y)] = rid

    current_z = getattr(gs, "map_pos", (0, 0, 0))[2]
    zs = sorted(layers.keys()) if (scope or "").strip().lower() == "all" else [current_z]

    out = []
    for z in zs:
        grid = layers[z]
        xs = [x for (x, _) in grid.keys()]
        ys = [y for (_, y) in grid.keys()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)

        out.append(f"Map (level z={z}):")

        for y in range(miny, maxy + 1):
            # Room row with east connectors (or east stubs)
            room_row_parts = []
            for x in range(minx, maxx + 1):
                rid = grid.get((x, y))
                if not rid:
                    room_row_parts.append("   ")
                    # east spacing
                    if x != maxx:
                        room_row_parts.append(" ")
                    continue

                r = gs.world.rooms[rid]
                is_here = (r == gs.room)
                has_up = "up" in r.exits
                has_down = "down" in r.exits

                # Cell glyph: [@], [o], [^], [v], [*]
                if is_here:
                    cell = "[@]"
                else:
                    if has_up and has_down:
                        cell = "[*]"
                    elif has_up:
                        cell = "[^]"
                    elif has_down:
                        cell = "[v]"
                    else:
                        cell = "[o]"
                room_row_parts.append(cell)

                # East connector / stub
                if x != maxx:
                    east_rid_mapped = grid.get((x + 1, y))
                    ex_e = r.exits.get("east")
                    if not ex_e:
                        room_row_parts.append(" ")
                    else:
                        if east_rid_mapped and ex_e.to == east_rid_mapped:
                            room_row_parts.append("=" if ex_e.locked else "-")
                        else:
                            # unexplored east exit (destination not on this layer map yet)
                            room_row_parts.append(">")
                # else (at right edge) nothing to append

            out.append("".join(room_row_parts).rstrip())

            # South connectors row with door/unknown markers
            conn_row_parts = []
            any_conn_row = False
            for x in range(minx, maxx + 1):
                rid = grid.get((x, y))
                if rid:
                    r = gs.world.rooms[rid]
                    ex_s = r.exits.get("south")
                    south_rid = grid.get((x, y + 1))
                    if ex_s and south_rid and ex_s.to == south_rid:
                        conn_row_parts.append(" ! " if ex_s.locked else " | ")
                        any_conn_row = True
                    elif ex_s:
                        # unexplored south exit from this room
                        conn_row_parts.append(" . ")
                        any_conn_row = True
                    else:
                        conn_row_parts.append("   ")
                else:
                    conn_row_parts.append("   ")

                if x != maxx:
                    conn_row_parts.append(" ")  # spacer between cells

            if any_conn_row:
                out.append("".join(conn_row_parts).rstrip())

        # Optional: small note for vertical exits from *current* room on this layer
        if z == current_z:
            ud = []
            r = gs.room
            if "up" in r.exits: ud.append("up")
            if "down" in r.exits: ud.append("down")
            if ud:
                out.append("Current room has vertical exits: " + " and ".join(ud))
        out.append("")

    # Add a compact legend
    out.append("Legend:")
    out.append("  [@]=you  [o]=room  [^]=up  [v]=down  [*]=up+down")
    out.append("  -/|=open corridor   =/!=locked door")
    out.append("  >=unexplored east exit   . =unexplored south exit")
    out.append("  (West/North exits to unmapped rooms will appear as east/south stubs once adjacent areas are mapped.)")

    return "\n".join(out)

                

def do_debug(gs) -> str:
    room = gs.room
    lines = [f"Room {room.id} ({room.name})"]
    for d, ex in room.exits.items():
        if ex.locked:
            lines.append(f"- {d}: to={ex.to} locked=True key_tag={ex.key_tag}")
        else:
            lines.append(f"- {d}: to={ex.to} locked=False")
    if gs.inv:
        invtags = [f"{i.name} tags={i.tags}" for i in gs.inv]
        lines.append("Inventory: " + "; ".join(invtags))
    else:
        lines.append("Inventory: (empty)")
    return "\n".join(lines)

# ---------- helpers ----------

_whitespace = re.compile(r"\s+")
_token = re.compile(r"[a-z0-9]+")

def _norm(s: str) -> str:
    return _whitespace.sub(" ", s.strip().lower())

def _tokens(s: str):
    return _token.findall(s.lower())

def _normalize_dir(text: str) -> str:
    if not text:
        return ""
    s = _norm(text)
    if s in DIR_SYNONYMS:
        return DIR_SYNONYMS[s]
    for tok in _tokens(s):
        if tok in ("north", "south", "east", "west", "up", "down"):
            return tok
        if tok in DIR_SYNONYMS:
            return DIR_SYNONYMS[tok]
    return ""

def _find_item(items, query):
    q = _norm(query)
    if not q:
        return None
    # exact/startswith
    for it in items:
        name = _norm(it.name)
        if name == q or name.startswith(q):
            return it
    # tag or token-subset
    q_tokens = set(_tokens(q))
    for it in items:
        name_tokens = set(_tokens(it.name))
        tag_tokens = set(_tokens(" ".join(it.tags)))
        if q_tokens.issubset(name_tokens | tag_tokens):
            return it
    # endswith fallback
    for it in items:
        if it.name.lower().endswith(q):
            return it
    return None

def _inventory_key_tags(gs):
    tags = []
    for it in gs.inv:
        for t in it.tags:
            if t.startswith("key:"):
                tags.append(t)
    return set(tags)

def _auto_unlock_with_inventory(gs, dir_target: str | None):
    keys = _inventory_key_tags(gs)
    if not keys:
        return []
    exits = gs.room.exits
    if dir_target:
        ex = exits.get(dir_target)
        if not ex:
            return []
        pairs = [(dir_target, ex)]
    else:
        pairs = list(exits.items())
    unlocked = []
    for d, ex in pairs:
        if ex.locked and ex.key_tag in keys:
            ex.locked = False
            unlocked.append(d)
            _unlock_reverse(gs, ex)
    return unlocked

def _unlocked_msg(unlocked_dirs):
    return f"You unlock the way {unlocked_dirs[0]}." if len(unlocked_dirs) == 1 \
           else "You unlock the ways " + ", ".join(unlocked_dirs) + "."

def _unlock_reverse(gs, ex):
    to_room = gs.world.rooms[ex.to]
    for d2, ex2 in to_room.exits.items():
        if ex2.to == gs.room.id:
            ex2.locked = False
            return

def _record_mapping(gs, direction: str, to_rid: str):
    """Assign coordinates to rooms as you move."""
    if not hasattr(gs, "map_coords") or gs.map_coords is None:
        gs.map_coords = {}
    if not hasattr(gs, "map_pos") or gs.map_pos is None:
        gs.map_pos = (0, 0, 0)
    # ensure current room has coords
    gs.map_coords.setdefault(gs.room.id, gs.map_pos)
    dx, dy, dz = DIR_DELTAS.get(direction, (0, 0, 0))
    x, y, z = gs.map_pos
    nx, ny, nz = x + dx, y + dy, z + dz
    # assign new room if unknown
    gs.map_coords.setdefault(to_rid, (nx, ny, nz))
    # move player position
    gs.map_pos = (nx, ny, nz)

