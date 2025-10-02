from adventure.engine.gen import make_world
from adventure.engine.parser import parse

def test_world_builds():
    w = make_world(seed=1234)
    assert w.start in w.rooms and len(w.rooms) >= 5

def test_parser_dirs():
    assert parse("n")[0] == "go"
    assert parse("go north")[1]["dir"] == "north"
