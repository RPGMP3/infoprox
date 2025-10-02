from adventure.engine.world import short_room_text
from adventure.engine.parser import DIR_SYNONYMS

def do_look(gs) -> str:
    room = gs.room
    room.seen = True
    return short_room_text(room)

def do_go(gs, direction: str) -> str:
    room = gs.room
    ex = room.exits.get(direction)
    if not ex:
        return "You can't go that way."
    if ex.locked:
        return "It's locked."
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
    if not item_name:
        return "Use what?"

    item = _find_item(gs.inv, item_name)
    if not item:
        return "You don't have that."

    # Keys are tagged like "key:brass1", "key:brass2"
    key_tags = [t for t in item.tags if t.startswith("key:")]
    if not key_tags:
        return "Nothing happens."

    # normalize optional target direction
    target = (target or "").strip().lower()
    if target in DIR_SYNONYMS:
        target = DIR_SYNONYMS[target]

    exits = gs.room.exits
    if target:
        ex = exits.get(target)
        if not ex:
            return "There's nothing like that here."
        pairs = [(target, ex)]
    else:
        pairs = list(exits.items())

    unlocked_dirs = []
    for d, ex in pairs:
        if ex.locked and ex.key_tag in key_tags:
            # unlock this exit
            ex.locked = False
            unlocked_dirs.append(d)
            # unlock the reverse exit (so you can return the way you came)
            to_room = gs.world.rooms[ex.to]
            for d2, ex2 in to_room.exits.items():
                if ex2.to == gs.room.id:
                    ex2.locked = False
                    break

    if unlocked_dirs:
        gs.score += 5
        if len(unlocked_dirs) == 1:
            return f"You unlock the way {unlocked_dirs[0]}."
        else:
            return "You unlock the ways " + ", ".join(unlocked_dirs) + "."

    # No unlock happened.
    # If there are locked exits here, hint that the key doesn't match.
    if any(ex.locked for ex in exits.values()):
        return "No matching locks here."

    return "Nothing happens."

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

def _find_item(items, query):
    query = query.lower()
    for it in items:
        if it.name.lower().startswith(query):
            return it
    return None

