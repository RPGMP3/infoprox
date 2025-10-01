import argparse
from adventure.engine.loop import start_game, load_game


def main():
    ap = argparse.ArgumentParser(prog="infoprox")
    sub = ap.add_subparsers(dest="cmd")
    play = sub.add_parser("play", help="Start a new game")
    play.add_argument("--seed", type=int, default=None, help="Optional RNG seed for worldgen")
    loadp = sub.add_parser("load", help="Load from a save file")
    loadp.add_argument("file")
    args = ap.parse_args()
    if args.cmd == "load":
        load_game(args.file)
    else:
        start_game(seed=args.seed)

if __name__ == "__main__":
    main()
