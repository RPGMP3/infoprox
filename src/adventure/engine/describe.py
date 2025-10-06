import random

THEME_FLAVOR = {
    "fantasy": {
        "great_hall": ["Banners stir in a draft.", "Footsteps echo off stone."],
        "archives": ["Dust motes hang in the lantern light.", "Old bindings creak softly."],
        "laboratory": ["Glassware clinks faintly.", "A herbal tang cuts the air."],
        "vault": ["The stone is cold to the touch.", "Locks nest like steel serpents."],
        "observatory": ["The ceiling is worked with constellations.", "A brass armillary ticks once."],
        "workshop": ["Shavings curl on the floor.", "Tools lie in careful disarray."],
        "catacombs": ["Names fade on the old markers.", "Stale air presses close."],
        "garden": ["Wind whispers in ivy.", "Faint petricor lingers."],
        "chapel": ["Candles gutter.", "A hush settles on the pews."],
        "library": ["Ink stains the desk.", "Loose pages rustle at nothing."],
    },
    "scifi": {
        "cryo_lab": ["Frost rims the seals.", "Status lights blink a patient green."],
        "server_room": ["Cold air hums through racks.", "Fiber optics pulse like veins."],
        "reactor_core": ["A low thrum vibrates the floor.", "Radiation shields glint dully."],
        "observation_deck": ["Stars spill across the viewport.", "Panels reflect pale light."],
        "cargo_bay": ["Mag clamps scar the deck.", "Crates bear hazard sigils."],
        "medbay": ["Antiseptic nips at your nose.", "Monitors blink quietly."],
        "maintenance": ["Coolant beads on pipes.", "Tools float in a netted pouch."],
        "command": ["Holo-screens ghost your reflection.", "Chairs sit at rigid attention."],
        "airlock": ["Warning stripes peel.", "A faint hiss betrays pressure."],
        "drone_hangar": ["Dull carapaces line the wall.", "Servos whine somewhere above."],
        "vault": ["Layers of composite plating overlap.", "The lock reads your silence."],
    },
    "horror": {
        "cellar": ["Moisture beads on stone.", "The smell of earth and iron."],
        "morgue": ["Drawers sit a little too still.", "Cold leeches up your legs."],
        "ward": ["Curtains stir without wind.", "A monitor clicks on and off."],
        "chapel": ["Pews list to one side.", "Wax pools like melted bone."],
        "attic": ["Rafters crowd low.", "Dust avalanches at your step."],
        "boiler_room": ["Pipes tick and settle.", "Heat breathes from the walls."],
        "ritual_chamber": ["Symbols scab the floor.", "An echo answers late."],
        "nursery": ["A mobile turns once.", "Paint flakes like ash."],
        "dining_room": ["Chairs face the wrong way.", "Utensils bite into wood."],
        "vault": ["Chains rasp across the floor.", "Something waits behind the door."],
    },
}

def _and_join(words):
    words = list(words)
    if not words: return ""
    if len(words) == 1: return words[0]
    return ", ".join(words[:-1]) + " and " + words[-1]

def _get_theme(room):
    for t in room.tags:
        if t.startswith("theme:"):
            return t.split(":", 1)[1]
    return "fantasy"

def _get_arch(room):
    for t in room.tags:
        if t.startswith("arch:"):
            return t.split(":", 1)[1]
    return None

def room_text(room, seen=False):
    rng = random.Random(room.id)
    theme = _get_theme(room)
    arch = _get_arch(room)

    first = f"You {'are' if seen else 'arrive'} in {room.name}."
    base = room.base_desc.rstrip(".")
    if base and base.lower() not in first.lower():
        first = f"{first} {base}."

    flavor_bits = []
    if arch and theme in THEME_FLAVOR and arch in THEME_FLAVOR[theme]:
        options = THEME_FLAVOR[theme][arch]
        if options:
            flavor_bits.append(rng.choice(options))

    if len(flavor_bits) > 2:
        flavor_bits = flavor_bits[:2]

    items = ""
    if room.items:
        names = _and_join(i.name for i in room.items)
        items = f"You see {names}."

    exits = _and_join(room.exits.keys()) or "nowhere"
    exits_line = f"Exits lead {exits}."

    parts = [first]
    if flavor_bits:
        parts.append(" ".join(flavor_bits))
    if items:
        parts.append(items)
    parts.append(exits_line)
    return " ".join(parts)

