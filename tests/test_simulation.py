import numpy as np
import pytest

from src.services.simulation import (
    MAX_ANGULAR_VELOCITY,
    MIN_ANGULAR_VELOCITY,
    clamp_angular_velocity,
    to_simulator_angular_velocity,
)


def test_clamp_angular_velocity_keeps_client_sign_and_clamps_magnitude():
    assert clamp_angular_velocity(np.pi / 2) == pytest.approx(np.pi / 2)
    assert clamp_angular_velocity(-np.pi / 2) == pytest.approx(-np.pi / 2)
    # magnitude clamped to [pi/6, pi/2]
    assert clamp_angular_velocity(1.0) == pytest.approx(1.0)
    assert clamp_angular_velocity(-0.1) == pytest.approx(-MIN_ANGULAR_VELOCITY)
    assert clamp_angular_velocity(10.0) == pytest.approx(MAX_ANGULAR_VELOCITY)
    # 0 counts as clockwise, like the original server (angular_velocity >= 0 -> cw)
    assert clamp_angular_velocity(0.0) == pytest.approx(MIN_ANGULAR_VELOCITY)


def test_to_simulator_angular_velocity_flips_sign_for_fcv1():
    # client: positive = cw; FCV1-Simulator: cw = -pi/2
    assert to_simulator_angular_velocity(np.pi / 2) == pytest.approx(-np.pi / 2)
    assert to_simulator_angular_velocity(-np.pi / 2) == pytest.approx(np.pi / 2)
    assert to_simulator_angular_velocity(0.0) == 0.0
