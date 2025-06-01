""" " Tests for the monitor module"""

from yaml import safe_load

from monitor import Connection, Monitor

test_host = "apollo"


def test_connect():
    with Connection(test_host) as conn:
        assert conn is not None


def test_color_code():
    values = [50, 60, 70]
    assert Monitor.color_code(-1, values) == -1
    assert Monitor.color_code(40, values) == 0
    assert Monitor.color_code(50, values) == 0
    assert Monitor.color_code(51, values) == 1

    assert Monitor.color_code(59, values) == 2
    assert Monitor.color_code(60, values) == 2
    assert Monitor.color_code(61, values) == 3

    assert Monitor.color_code(69, values) == 4
    assert Monitor.color_code(70, values) == 4
    assert Monitor.color_code(71, values) == 5


def test_probe():
    with open("monitor.yaml") as file:
        config = safe_load(file)
    with Connection(test_host) as conn:
        for s in config.get("sensors").values():
            if conn is None:
                return
            name = s.get("name")
            cmd = s.get("cmd")
            values = s.get("values")
            instance = Monitor.create_instance(name, conn, cmd, values)
            val, col = instance.probe()
            assert col != -1 and val != -1
