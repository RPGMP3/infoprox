# Infoprox


Procedural, Infocom‑style text adventure. Deterministic worldgen via RNG seed, classic verb‑noun parser, inventory, keys/locks, and save/load.


## Quickstart (WSL)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
infoprox play --seed 1234
# or
python -m adventure.cli play --seed 1234
