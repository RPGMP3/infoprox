import re

VERBS = {
    "go": ["go", "move", "walk", "run"],
    "look": ["look", "l", "examine", "inspect", "x", "look at"],
    "take": ["take", "get", "grab", "pick up"],
    "drop": ["drop", "leave", "put"],
    "inventory": ["inventory", "i"],
    "use": ["use", "unlock", "open"],  # 'open' will try keys automatically if no item given
    "help": ["help", "?"],
    "save": ["save"],
    "load": ["load"],
    "quit": ["quit", "exit"],
    "debug": ["debug","dev","diag"],
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

    # direction-only
    if cmd in DIR_SYNONYMS:
        return ("go", {"dir": DIR_SYNONYMS[cmd]})
    if cmd in ("north", "south", "east", "west", "up", "down"):
        return ("go", {"dir": cmd})

    # verb resolution (match longest synonym first to catch "look at")
    for k, syns in VERBS.items():
        for s in sorted(syns, key=len, reverse=True):
            if cmd == s or cmd.startswith(s + " "):
                rest = cmd[len(s):].strip()
                return (k, _args_for(k, rest))

    return ("unknown", {"raw": cmd})

def _args_for(verb: str, rest: str):
    if verb == "go":
        if rest in DIR_SYNONYMS:
            rest = DIR_SYNONYMS[rest]
        return {"dir": rest}

    if verb == "look":
        # support "look at <thing>" and "examine <thing>"
        if rest.startswith("at "):
            rest = rest[3:].strip()
        return {"item": rest}  # may be empty -> room look

    if verb in ("inventory", "help", "quit", "save", "load"):
        return {"rest": rest}

    if verb in ("take", "drop"):
        return {"item": rest}

    if verb == "use":
        # allow: "use key on door"
        m = re.match(r"(\w[\w\s\-]*)?(?:\s+on\s+(\w[\w\s\-]*))?$", rest or "")
        item = (m.group(1) or "").strip() if m else ""
        target = (m.group(2) or "").strip() if m else ""
        return {"item": item, "target": target}

    return {"rest": rest}

