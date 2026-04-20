"""Tests for the main module"""

from main import calculate_position


def test_calculate_position():
    # Mode 1: one host with 32 sensors, filled row-wise
    assert calculate_position(1, 0, 0) == (0, 0)
    assert calculate_position(1, 0, 1) == (1, 0)
    assert calculate_position(1, 0, 31) == (7, 3)

    # Mode 2: four hosts with eight sensors each : one row per host
    assert calculate_position(2, 0, 0) == (0, 0)
    assert calculate_position(2, 0, 7) == (7, 0)
    assert calculate_position(2, 1, 0) == (0, 1)
    assert calculate_position(2, 1, 7) == (7, 1)
    assert calculate_position(2, 2, 0) == (0, 2)
    assert calculate_position(2, 2, 7) == (7, 2)
    assert calculate_position(2, 3, 0) == (0, 3)
    assert calculate_position(2, 3, 7) == (7, 3)

    # Mode 3: eight hosts with four sensors each : one column per host
    assert calculate_position(3, hi=0, si=0) == (0, 0)
    assert calculate_position(3, hi=0, si=3) == (0, 3)
    assert calculate_position(3, hi=7, si=0) == (7, 0)
    assert calculate_position(3, hi=7, si=3) == (7, 3)

    # Mode 4: thirty-two hosts with one sensor each, filled row-wise
    assert calculate_position(4, hi=0, si=0) == (0, 0)
    assert calculate_position(4, hi=1, si=0) == (1, 0)
    assert calculate_position(4, hi=31, si=0) == (7, 3)
