from adventure.engine.world import short_room_text

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
    # Unlock any matching exit by key tag
    for d, ex in gs.room.exits.items():
        if ex.locked and ex.key_tag and ex.key_tag in item.tags:
            ex.locked = False
            gs.score += 5
            return f"You unlock the way {d}."
    return "Nothing happens."

def _find_item(items, query: str):
    q = (query or "").lower()
    for it in items:
        if it.name.lower().startswith(q):
            return it
    return None

