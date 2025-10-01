import json
from dataclasses import asdict




def save_game(gs, filename="save.json"):
data = {
"seed": gs.world.seed,
"room": gs.room.id,
"score": gs.score,
"inv": [asdict(i) for i in gs.inv],
"rooms": {
rid: {
"seen": r.seen,
"items": [asdict(i) for i in r.items],
"exits": {d: {"locked": ex.locked} for d, ex in r.exits.items()},
}
for rid, r in gs.world.rooms.items()
},
}
with open(filename, "w") as f:
json.dump(data, f, indent=2)
return f"Game saved to {filename}."




def load_state(world, data):
from adventure.engine.world import Item


for rid, rdata in data["rooms"].items():
r = world.rooms[rid]
r.seen = rdata["seen"]
r.items = [Item(**it) for it in rdata["items"]]
for d, ed in rdata["exits"].items():
world.rooms[rid].exits[d].locked = ed["locked"]
