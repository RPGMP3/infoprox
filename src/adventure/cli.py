import argparse
from adventure.engine.loop import start_game, load_game

def main():
    ap = argparse.ArgumentParser(prog="infoprox")
    sub = ap.add_subparsers(dest="cmd")

    # play subcommand
    play = sub.add_parser("play", help="Start a new game")
    play.add_argument("--seed", type=int, default=None, help="Optional RNG seed")
    play.add_argument(
        "--theme",
        choices=["fantasy", "scifi", "horror"],
        default=None,
        help="World theme (default: prompt at start)",
    )
    play.add_argument(
        "--rooms",
        type=int,
        default=15,
        help="Number of rooms (clamped 10–20, default 15)",
    )

    # load subcommand
    loadp = sub.add_parser("load", help="Load from a save file")
    loadp.add_argument("file")

    args = ap.parse_args()

    if args.cmd == "load":
        load_game(args.file)
    else:
        rooms = max(10, min(20, int(args.rooms or 15)))
        start_game(seed=args.seed, theme=args.theme, rooms=rooms)

if __name__ == "__main__":
    main()

