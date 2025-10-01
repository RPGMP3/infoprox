from dataclasses import dataclass, field
import json
from typing import Any

from adventure.engine.gen import make_world
from adventure.engine.parser import parse
from adventure.engine.actions import do_go, do_inventory, do_look, do_take, do_use
from adventure.engine.save import save_game, load_state
from adventure.engine.world import Item


@dataclass
class GameState:
    world: Any
    room: Any
    inv: list = field(default_factory=list)
    score: int = 0
    turns: int = 0


def start_game(seed=None):
    world = make_world(seed=seed)
    gs = GameState(world=world, room=world.rooms[world.start])
    print(banner(world.seed))
    print(do_look(gs))
    loop(gs)


def load_game(file):
    with open(file) as f:
        data = json.load(f)
    world = make_world(seed=data["seed"])
    gs = GameState(world=world, room=world.rooms[data["room"]])
    gs.score = data.get("score", 0)
    gs.inv = [Item(**it) for it in data.get("inv", [])]
    load_state(world, data)
    print(banner(world.seed, loaded=True))
    print(do_look(gs))
    loop(gs)


def loop(gs: GameState):
    while True:
        try:
            cmd = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            print(f"Score: {gs.score}  Turns: {gs.turns}")
            break

        verb, args = parse(cmd)
        gs.turns += 1

        if verb == "help":
            print("Commands: look/l, go <dir>, n/s/e/w/u/d, take <item>, use <item> [on <target>], inventory/i, save, load, quit")
            continue
        if verb == "look":
            print(do_look(gs)); continue
        if verb == "inventory":
            print(do_inventory(gs)); continue
        if verb == "go":
            print(do_go(gs, args.get("dir", ""))); continue
        if verb == "take":
            print(do_take(gs, args.get("item", ""))); continue
        if verb == "use":
            print(do_use(gs, args.get("item", ""), args.get("target", ""))); continue
        if verb == "save":
            filename = args.get("rest") or "save.json"
            print(save_game(gs, filename)); continue
        if verb == "load":
            print("Use the CLI: infoprox load save.json"); continue
        if verb == "quit":
            print(f"Score: {gs.score}  Turns: {gs.turns}"); break
        if verb == "unknown":
            print("I don't understand that."); continue


def banner(seed, loaded: bool = False) -> str:
    state = "Loaded game." if loaded else "New game."
    # ASCII-only to avoid any copy/paste issues
    return f"INFOPROX - {state} Seed {seed}. Type 'help' for commands."

