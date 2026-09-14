from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from src.models.dc_models import ShotInfoModel
from src.models.schema_models import StateSchema

if TYPE_CHECKING:
    from src.simulator import StoneSimulator

# Angular velocity conventions:
# - Client / DB / last_move: positive = clockwise (dc4client sends +pi/2 for "cw").
# - FCV1-Simulator (>= v1.0.30 takes the value as-is): counter-clockwise positive,
#   i.e. cw = -pi/2. The sign is flipped here, and only here.
MIN_ANGULAR_VELOCITY = np.pi / 6
MAX_ANGULAR_VELOCITY = np.pi / 2


def clamp_angular_velocity(angular_velocity: float) -> float:
    """Clamp the magnitude to [pi/6, pi/2], keeping the client's sign (0 counts as clockwise)."""
    spin_sign = 1.0 if angular_velocity >= 0 else -1.0
    magnitude = float(np.clip(abs(angular_velocity), MIN_ANGULAR_VELOCITY, MAX_ANGULAR_VELOCITY))
    return spin_sign * magnitude


def to_simulator_angular_velocity(angular_velocity: float) -> float:
    """Convert a client-convention angular velocity to the simulator's (ccw positive)."""
    return -angular_velocity


def simulate_fcv1(
    *,
    shot_info: ShotInfoModel,
    state_data: StateSchema,
    total_shot_number: int,
    shot_per_team: int,
    team_number: int,
    applied_rule: int,
    stone_simulator: StoneSimulator,
) -> tuple[np.ndarray, np.ndarray]:
    """Run one shot simulation (fcv1).

    This is intentionally kept outside the HTTP router module.
    """

    velocity_x: np.float64 = shot_info.translational_velocity * np.cos(shot_info.shot_angle)
    velocity_y: np.float64 = shot_info.translational_velocity * np.sin(shot_info.shot_angle)

    stone_position = np.array(
        [
            coordinate
            for _, stones in state_data.stone_coordinate.data.items()
            for stone in stones
            for coordinate in (stone["x"], stone["y"])
        ]
    )

    simulated_stones_coordinate, trajectory = stone_simulator.simulator(
        stone_position,
        total_shot_number,
        velocity_x,
        velocity_y,
        to_simulator_angular_velocity(shot_info.angular_velocity),
        team_number,
        shot_per_team,
        applied_rule,
    )
    return simulated_stones_coordinate, trajectory
