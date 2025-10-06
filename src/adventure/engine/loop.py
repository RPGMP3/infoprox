from dataclasses import dataclass, field
import json
from typing import Any

from adventure.engine.gen import make_world
from adventure.engine.parser import parse
from adventure.engine.actions import (
    do_go, do_inventory, do_look, do_take, do_use,
    do_debug, do_examine, do_read, do_map
)
from adventure.engine.save import save_game, load_state
from adventure.engine.world import Item

@dataclass
class GameState:
    world: Any
    room: Any
    inv: list = field(default_factory=list)
    score: int = 0
    turns: int = 0
    map_coords: dict = field(default_factory=dict)   # NEW
    map_pos: tuple = (0, 0, 0)                       # NEW

def _prompt_theme():
    while True:
        sel = input("Choose a theme [fantasy/scifi/horror] (default: fantasy): ").strip().lower()
        if sel == "": return "fantasy"
        if sel in ("fantasy", "scifi", "horror"):
            return sel
        print("Please type: fantasy, scifi, or horror.")

def start_game(seed=None, theme=None, rooms=15):
    theme = theme or _prompt_theme()
    world = make_world(seed=seed, n_rooms=rooms, theme=theme)
    gs = GameState(world=world, room=world.rooms[world.start])
    # init mapping at origin
    gs.map_coords[gs.room.id] = (0, 0, 0)
    gs.map_pos = (0, 0, 0)

    print(banner(world.seed, theme=world.theme))
    print(do_look(gs))
    loop(gs)

def load_game(file):
    with open(file) as f:
        data = json.load(f)
    theme = data.get("theme", "fantasy")
    n_rooms = int(data.get("n_rooms", 15))
    world = make_world(seed=data["seed"], n_rooms=n_rooms, theme=theme)

    gs = GameState(world=world, room=world.rooms[data["room"]])
    gs.score = data.get("score", 0)
    gs.inv = [Item(**it) for it in data.get("inv", [])]
    load_state(world, data)

    # mapping starts at origin for the loaded room; it will fill as you move
    gs.map_coords[gs.room.id] = (0, 0, 0)
    gs.map_pos = (0, 0, 0)

    print(banner(world.seed, loaded=True, theme=world.theme))
    print(do_look(gs))
    loop(gs)

def loop(gs):
    while True:
        cmd = input("\n> ").strip()
        verb, args = parse(cmd)
        gs.turns += 1
        if verb == "help":
            print("Commands: look/l, go <dir>, n/s/e/w/u/d, take <item>, use/unlock [<item>] [on <dir>], examine/x <item>, read <item>, inventory/i, map [all], save, load, quit, debug")
            continue
        if verb == "look":
            print(do_look(gs)); continue
        if verb == "inventory":
            print(do_inventory(gs)); continue
        if verb == "go":
            print(do_go(gs, args.get("dir",""))); continue
        if verb == "take":
            print(do_take(gs, args.get("item",""))); continue
        if verb == "use":  # unlock handled here too
            print(do_use(gs, args.get("item",""), args.get("target",""))); continue
        if verb == "examine":
            print(do_examine(gs, args.get("item",""))); continue
        if verb == "read":
            print(do_read(gs, args.get("item",""))); continue
        if verb == "map":
            print(do_map(gs, args.get("rest",""))); continue
        if verb == "save":
            print(save_game(gs)); continue
        if verb == "load":
            print("Use the CLI: infoprox load save.json"); continue
        if verb == "quit":
            print(f"Score: {gs.score}  Turns: {gs.turns}"); break
        if verb == "debug":
            print(do_debug(gs)); continue
        if verb == "unknown":
            print("I don't understand that."); continue
        print("...")

def banner(seed, loaded=False, theme="fantasy"):
    state = "Loaded game." if loaded else "New game."
    goal = {
        "fantasy": "Goal: place 3 relics and open the Sanctum gate.",
        "scifi":   "Goal: install 3 modules to unlock the Core Chamber.",
        "horror":  "Goal: present 3 mementos to quiet the Sealed Door.",
    }.get(theme, "Goal: find 3 artifacts, then open the vault gate.")
    return f"INFOPROX - {state} Seed {seed}. Theme: {theme}.\n{goal}"



