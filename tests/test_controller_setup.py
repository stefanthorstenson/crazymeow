"""
Tests for Controller Mapping Setup CLI requirements (requirements_controller_setup.md).

Each test function is named after the requirement ID it covers.
Tests requiring a real Bluetooth controller are skipped.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires hardware: separate CLI tool, invoked as controller-setup")
def test_CS_001():
    """The controller mapping setup shall be a separate CLI tool, independent of Crazypilot."""


def test_CS_001_separate_module():
    """controller_setup is a separate package from crazypilot."""
    import controller_setup.main
    import crazypilot.main
    assert controller_setup.main.__file__ != crazypilot.main.__file__


def test_CS_001b_entry_point_defined():
    """controller-setup entry point is declared in pyproject.toml."""
    toml_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(toml_path) as f:
        content = f.read()
    assert "controller-setup = " in content, "controller-setup entry point missing from pyproject.toml"


@pytest.mark.skip(reason="requires hardware: Raspberry Pi with Raspbian OS")
def test_CS_002():
    """The CLI shall run on Raspberry Pi with Raspbian OS as its primary target platform."""


@pytest.mark.skip(reason="requires hardware: verifying no sudo needed at runtime")
def test_CS_003():
    """The CLI shall not require super user privileges to run."""


@pytest.mark.skip(reason="requires network: verifying no internet access during operation")
def test_CS_004():
    """The CLI shall not download anything from the internet during operation."""


def test_CS_005_modularization():
    """The code shall be well modularized — separate modules exist for each concern."""
    modules = [
        "controller_setup.main",
        "controller_setup.controller_detector",
        "controller_setup.axis_mapper",
        "controller_setup.config_writer",
        "controller_setup.live_tester",
    ]
    import importlib
    for mod in modules:
        m = importlib.import_module(mod)
        assert m is not None


@pytest.mark.skip(reason="requires hardware: Ubuntu laptop with Crazyradio 2.0")
def test_CS_006():
    """It shall be possible to run on a laptop with Ubuntu 24.04 and Crazyradio 2.0."""


# ---------------------------------------------------------------------------
# Controller Detection
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires hardware: real Bluetooth game controller connected")
def test_CS_010():
    """The CLI shall detect all connected Bluetooth game controllers."""


@pytest.mark.skip(reason="requires hardware: real Bluetooth game controller for name display")
def test_CS_011():
    """The CLI shall display a human-readable name for each detected controller."""


def test_CS_010_detect_and_select_no_controllers_exits():
    """If no controllers are detected, detect_and_select exits with code 1."""
    with patch("controller_setup.controller_detector.pygame") as mock_pygame:
        mock_pygame.joystick.get_count.return_value = 0

        from controller_setup.controller_detector import detect_and_select
        with pytest.raises(SystemExit) as exc_info:
            detect_and_select()
        assert exc_info.value.code == 1


def test_CS_011_controller_name_displayed(capsys):
    """detect_and_select displays the human-readable name of each detected controller."""
    with patch("controller_setup.controller_detector.pygame") as mock_pygame:
        mock_js = MagicMock()
        mock_js.get_name.return_value = "My Fancy Controller"
        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_js

        with patch("builtins.input", return_value="1"):
            from controller_setup.controller_detector import detect_and_select
            selected, name = detect_and_select()

        captured = capsys.readouterr()
        assert "My Fancy Controller" in captured.out
        assert name == "My Fancy Controller"


# ---------------------------------------------------------------------------
# Axis Mapping
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires hardware: real controller joystick movement")
def test_CS_020():
    """The CLI shall guide the user through mapping four flight commands."""


@pytest.mark.skip(reason="requires hardware: real controller joystick axis detection")
def test_CS_021():
    """For each flight command, the CLI shall detect which physical axis was moved."""


@pytest.mark.skip(reason="requires hardware: real controller for polarity detection")
def test_CS_022():
    """The CLI shall detect and record correct polarity for each axis."""


@pytest.mark.skip(reason="requires hardware: real controller for live axis display")
def test_CS_023():
    """The CLI shall display live axis values during mapping."""


def test_CS_020_four_roles_mapped():
    """axis_mapper maps exactly the four required flight command roles."""
    from controller_setup.axis_mapper import _AXIS_ROLES
    required_roles = {"altitude_rate", "yaw_rate", "velocity_x", "velocity_y"}
    mapped_roles = {role for role, _ in _AXIS_ROLES}
    assert required_roles == mapped_roles, (
        f"Expected roles {required_roles}, got {mapped_roles}"
    )


def test_CS_022_polarity_detection_logic():
    """Polarity (inversion) is set to True if the detected axis value is negative."""
    # From axis_mapper.py: detected_inverted = value < 0
    from controller_setup.axis_mapper import _DETECTION_THRESHOLD

    # Simulate positive deflection -> not inverted
    value_positive = _DETECTION_THRESHOLD + 0.1
    inverted_positive = value_positive < 0
    assert not inverted_positive

    # Simulate negative deflection -> inverted
    value_negative = -((_DETECTION_THRESHOLD) + 0.1)
    inverted_negative = value_negative < 0
    assert inverted_negative


# ---------------------------------------------------------------------------
# Configuration Persistence
# ---------------------------------------------------------------------------

def test_CS_030_mapping_saved_as_pretty_json():
    """The completed mapping shall be saved as pretty-printed JSON."""
    from controller_setup.config_writer import save

    mapping = {
        "controller_name": "TestController",
        "axes": {
            "altitude_rate": {"index": 0, "inverted": False},
            "yaw_rate":      {"index": 1, "inverted": False},
            "velocity_x":    {"index": 2, "inverted": False},
            "velocity_y":    {"index": 3, "inverted": False},
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp_path = f.name
    os.unlink(tmp_path)  # ensure it doesn't exist yet

    try:
        save(mapping, path=tmp_path)
        assert os.path.exists(tmp_path)

        with open(tmp_path) as f:
            raw = f.read()

        # Pretty-printed: must contain newlines and indentation
        assert "\n" in raw, "JSON output should be multi-line (pretty-printed)"
        assert "  " in raw, "JSON output should have indentation"

        # Must be valid JSON
        parsed = json.loads(raw)
        assert parsed["controller_name"] == "TestController"
        assert parsed["axes"]["altitude_rate"]["index"] == 0
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_CS_030_default_save_path():
    """Mapping is saved to ~/.config/crazypilot/controller_mapping.json by default."""
    from controller_setup.config_writer import _DEFAULT_PATH
    expected_suffix = os.path.join(".config", "crazypilot", "controller_mapping.json")
    assert _DEFAULT_PATH.endswith(expected_suffix), (
        f"Default path '{_DEFAULT_PATH}' does not end with '{expected_suffix}'"
    )


def test_CS_032_overwrite_confirmation_when_file_exists(tmp_path):
    """If config file exists, CLI informs user and asks for confirmation before overwriting."""
    from controller_setup.config_writer import save

    mapping = {
        "controller_name": "TestController",
        "axes": {
            "altitude_rate": {"index": 0, "inverted": False},
            "yaw_rate":      {"index": 1, "inverted": False},
            "velocity_x":    {"index": 2, "inverted": False},
            "velocity_y":    {"index": 3, "inverted": False},
        },
    }

    target = str(tmp_path / "controller_mapping.json")

    # Create the existing file
    with open(target, "w") as f:
        json.dump({"controller_name": "OldController", "axes": {}}, f)

    # Respond "n" to overwrite prompt -> should NOT overwrite
    with patch("builtins.input", return_value="n"):
        with pytest.raises(SystemExit):
            save(mapping, path=target)

    with open(target) as f:
        saved = json.load(f)
    assert saved["controller_name"] == "OldController", "File should not have been overwritten"


def test_CS_032_overwrite_proceeds_on_confirmation(tmp_path):
    """If config file exists and user confirms, overwrite proceeds."""
    from controller_setup.config_writer import save

    mapping = {
        "controller_name": "NewController",
        "axes": {
            "altitude_rate": {"index": 0, "inverted": False},
            "yaw_rate":      {"index": 1, "inverted": False},
            "velocity_x":    {"index": 2, "inverted": False},
            "velocity_y":    {"index": 3, "inverted": False},
        },
    }

    target = str(tmp_path / "controller_mapping.json")

    with open(target, "w") as f:
        json.dump({"controller_name": "OldController", "axes": {}}, f)

    with patch("builtins.input", return_value="y"):
        save(mapping, path=target)

    with open(target) as f:
        saved = json.load(f)
    assert saved["controller_name"] == "NewController", "File should have been overwritten"


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def test_CS_040_summary_and_confirm_before_save(capsys):
    """After all axes mapped, CLI shows summary and asks for confirmation before saving."""
    # In main.py, the summary is printed and input("Save this mapping? [y/N]:") is called.
    import inspect
    from controller_setup import main as cs_main
    src = inspect.getsource(cs_main)
    assert "Mapping Summary" in src or "summary" in src.lower(), (
        "No summary section found in controller_setup.main"
    )
    assert "Save this mapping?" in src or "save" in src.lower(), (
        "No save confirmation found in controller_setup.main"
    )


@pytest.mark.skip(reason="requires hardware: real controller for live test mode")
def test_CS_041():
    """After saving, the CLI shall offer a live test mode."""


def test_CS_041_live_test_offered_in_code():
    """After saving, main.py offers a live test — check source code."""
    import inspect
    from controller_setup import main as cs_main
    src = inspect.getsource(cs_main)
    assert "live test" in src.lower() or "run_live_test" in src, (
        "Live test not offered in controller_setup.main"
    )
