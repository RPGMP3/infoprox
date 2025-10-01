import re

VERBS = {
    "go": ["go", "move", "walk", "run"],
    "look": ["look", "l", "examine", "x"],
    "take": ["take", "get", "grab"],
    "inventory": ["inventory", "i"],
    "use": ["use", "unlock", "open"],
    "help": ["help", "?"],
    "save": ["save"],
    "load": ["load"],
    "quit": ["quit", "exit"],
}

DIR_SYNONYMS = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "u": "up",
    "d": "down",
}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def parse(cmd: str):
    cmd = normalize(cmd)
    if not cmd:
        return ("none", {})

    # single-letter or full direction
    if cmd in DIR_SYNONYMS:
        return ("go", {"dir": DIR_SYNONYMS[cmd]})
    if cmd in ("north", "south", "east", "west", "up", "down"):
        return ("go", {"dir": cmd})

    # verb resolution
    for k, syns in VERBS.items():
        for s in syns:
            if cmd == s or cmd.startswith(s + " "):
                rest = cmd[len(s):].strip()
                return (k, _args_for(k, rest))

    return ("unknown", {"raw": cmd})

def _args_for(verb: str, rest: str):
    if verb == "go":
        if rest in DIR_SYNONYMS:
            rest = DIR_SYNONYMS[rest]
        return {"dir": rest}
    if verb in ("look", "inventory", "help", "quit", "save", "load"):
        return {"rest": rest}
    if verb in ("take", "use"):
        # allow: "use key on door"
        m = re.match(r"(\w[\w\s\-]*)?(?:\s+on\s+(\w[\w\s\-]*))?$", rest or "")
        item = (m.group(1) or "").strip() if m else ""
        target = (m.group(2) or "").strip() if m else ""
        return {"item": item, "target": target}
    return {"rest": rest}

