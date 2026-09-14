import pytest

from src.domain.match_rules import (
    MD_POSITIONED_STONE_GUARD,
    MD_POSITIONED_STONES_PATTERN_COUNT,
    MD_POWER_PLAY_GUARD,
    generate_mixed_doubles_initial_stones,
    generate_reset_stone_coordinate_data,
    stone_count_per_team,
    total_shots_per_end,
)


def test_stone_count_per_team():
    assert stone_count_per_team("standard") == 8
    assert stone_count_per_team("mixed_doubles") == 6


def test_total_shots_per_end():
    assert total_shots_per_end("standard") == 16
    assert total_shots_per_end("mixed_doubles") == 10


def test_generate_reset_stone_coordinate_data_standard():
    data = generate_reset_stone_coordinate_data("standard")
    assert set(data.keys()) == {"team0", "team1"}
    assert len(data["team0"]) == 8
    assert len(data["team1"]) == 8
    assert all(coord == {"x": 0.0, "y": 0.0} for coord in data["team0"])
    assert all(coord == {"x": 0.0, "y": 0.0} for coord in data["team1"])


def test_generate_reset_stone_coordinate_data_mixed_doubles():
    data = generate_reset_stone_coordinate_data("mixed_doubles")
    assert set(data.keys()) == {"team0", "team1"}
    assert len(data["team0"]) == 6
    assert len(data["team1"]) == 6


def test_generate_mixed_doubles_initial_stones_invalid_pattern_raises():
    with pytest.raises(ValueError):
        generate_mixed_doubles_initial_stones(
            hammer_team_name="team0",
            power_play_side=None,
            positioned_stones_pattern=-1,
        )

    with pytest.raises(ValueError):
        generate_mixed_doubles_initial_stones(
            hammer_team_name="team0",
            power_play_side=None,
            positioned_stones_pattern=8,
        )


def test_mixed_doubles_guard_tables_follow_2026_27_markings():
    # Four marks 2 ft apart, each giving a house-side and a hack-side position.
    assert MD_POSITIONED_STONES_PATTERN_COUNT == 8
    assert len(MD_POSITIONED_STONE_GUARD) == 8
    assert len(MD_POWER_PLAY_GUARD) == 8

    ys = [y for _, y in MD_POSITIONED_STONE_GUARD]
    assert ys == pytest.approx([35.350, 35.060, 34.740, 34.450, 34.130, 33.840, 33.520, 33.230])

    # Centre guard is always on the centre line.
    assert all(x == 0.0 for x, _ in MD_POSITIONED_STONE_GUARD)

    # Power play guard shares y with the centre guard and its x lies on the line
    # from the hack midpoint (0, 0) to the tee line / 8-foot intersection (1.219, 38.405).
    for (_, y_center), (x_pp, y_pp) in zip(MD_POSITIONED_STONE_GUARD, MD_POWER_PLAY_GUARD):
        assert y_pp == y_center
        assert x_pp == pytest.approx(1.219 * y_pp / 38.405, abs=0.0005)
    assert [x for x, _ in MD_POWER_PLAY_GUARD] == pytest.approx(
        [1.122, 1.113, 1.103, 1.093, 1.083, 1.074, 1.064, 1.055]
    )


def test_generate_mixed_doubles_initial_stones_uses_pattern_for_guard():
    for pattern, (x, y) in enumerate(MD_POSITIONED_STONE_GUARD):
        data = generate_mixed_doubles_initial_stones(
            hammer_team_name="team0",
            power_play_side=None,
            positioned_stones_pattern=pattern,
            hammer_stone_position="house",
        )
        # Non-hammer (team1) gets the guard.
        assert data["team1"][0]["x"] == pytest.approx(x)
        assert data["team1"][0]["y"] == pytest.approx(y)

    for pattern, (x, y) in enumerate(MD_POWER_PLAY_GUARD):
        data = generate_mixed_doubles_initial_stones(
            hammer_team_name="team0",
            power_play_side="right",
            positioned_stones_pattern=pattern,
            hammer_stone_position="house",
        )
        assert data["team1"][0]["x"] == pytest.approx(x)
        assert data["team1"][0]["y"] == pytest.approx(y)


def test_generate_mixed_doubles_initial_stones_hammer_gets_house_when_requested():
    data = generate_mixed_doubles_initial_stones(
        hammer_team_name="team0",
        power_play_side=None,
        positioned_stones_pattern=0,
        hammer_stone_position="house",
    )

    # Function returns 8 slots per team for simulator compatibility.
    assert len(data["team0"]) == 8
    assert len(data["team1"]) == 8

    # When hammer_stone_position="house", hammer gets the house stone at index 0.
    assert data["team0"][0]["x"] == pytest.approx(0.0)
    assert data["team0"][0]["y"] == pytest.approx(38.870)


def test_generate_mixed_doubles_initial_stones_power_play_left_flips_x():
    left = generate_mixed_doubles_initial_stones(
        hammer_team_name="team0",
        power_play_side="left",
        positioned_stones_pattern=0,
        hammer_stone_position="house",
    )
    right = generate_mixed_doubles_initial_stones(
        hammer_team_name="team0",
        power_play_side="right",
        positioned_stones_pattern=0,
        hammer_stone_position="house",
    )

    # House stone x should be negative on left and positive on right.
    assert left["team0"][0]["x"] < 0
    assert right["team0"][0]["x"] > 0
    assert left["team0"][0]["y"] == pytest.approx(right["team0"][0]["y"])


def test_generate_mixed_doubles_initial_stones_invalid_hammer_stone_position_raises():
    with pytest.raises(ValueError):
        generate_mixed_doubles_initial_stones(
            hammer_team_name="team0",
            power_play_side=None,
            positioned_stones_pattern=0,
            hammer_stone_position="invalid",
        )
