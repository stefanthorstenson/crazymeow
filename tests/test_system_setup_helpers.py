"""
Tests for System Setup Helpers requirements (requirements_system_setup_helpers.md).

Each test function is named after the requirement ID it covers.
Tests requiring real hardware (Raspberry Pi, USB Crazyflie, systemd, sudo) are skipped.
"""

import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scripts_dir():
    return os.path.join(os.path.dirname(__file__), "..", "scripts")


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires hardware: Raspberry Pi with Raspbian OS")
def test_SS_001():
    """System setup helpers shall run on Raspberry Pi with Raspbian OS."""


def test_SS_002_modularization():
    """System setup helpers shall be well modularized — separate scripts exist."""
    scripts = [
        "configure_crazyflie.py",
        "setup_dependencies.py",
        "setup_services.py",
        "setup_ssh.py",
        "test_connection.py",
    ]
    scripts_dir = _scripts_dir()
    for script in scripts:
        path = os.path.join(scripts_dir, script)
        assert os.path.exists(path), f"Script not found: {path}"

    # Shared utils are in a submodule
    utils_dir = os.path.join(scripts_dir, "utils")
    assert os.path.exists(os.path.join(utils_dir, "sudo_helper.py")), "sudo_helper.py missing"
    assert os.path.exists(os.path.join(utils_dir, "git_helper.py")), "git_helper.py missing"


def test_SS_003_sudo_prints_description_and_prompts():
    """Before each sudo call, tool shall print description and wait for confirmation."""
    from scripts.utils.sudo_helper import run_sudo

    printed_lines = []
    inputs = iter(["n"])  # decline to run

    def fake_print(*args, **kwargs):
        printed_lines.append(" ".join(str(a) for a in args))

    with patch("builtins.print", side_effect=fake_print), \
         patch("builtins.input", side_effect=inputs):
        run_sudo(["sudo", "echo", "hello"], "Test sudo description")

    # The description must appear in output
    combined = " ".join(printed_lines)
    assert "Test sudo description" in combined, (
        f"Description not found in printed output: {printed_lines}"
    )


def test_SS_003_sudo_runs_command_on_confirmation():
    """run_sudo executes the command when user confirms with 'y'."""
    from scripts.utils.sudo_helper import run_sudo

    with patch("builtins.input", return_value="y"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_sudo(["sudo", "echo", "hello"], "Test run")
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["sudo", "echo", "hello"]


def test_SS_003_sudo_skips_command_on_decline():
    """run_sudo does NOT execute the command when user declines."""
    from scripts.utils.sudo_helper import run_sudo

    with patch("builtins.input", return_value="n"), \
         patch("subprocess.run") as mock_run:
        run_sudo(["sudo", "echo", "hello"], "Test skip")
        mock_run.assert_not_called()


def test_SS_004_git_clone_prints_repo_and_prompts():
    """Before git clone, tool shall inform user of repo and prompt for confirmation."""
    from scripts.utils.git_helper import clone

    printed_lines = []
    with patch("builtins.print", side_effect=lambda *a, **kw: printed_lines.append(" ".join(str(x) for x in a))), \
         patch("builtins.input", return_value="n"):
        clone("https://github.com/example/repo.git", "/tmp/test-repo", "Clone test repo")

    combined = " ".join(printed_lines)
    assert "https://github.com/example/repo.git" in combined, (
        f"Repository URL not found in output: {printed_lines}"
    )


def test_SS_004_git_clone_runs_on_confirmation():
    """git clone executes when user confirms."""
    from scripts.utils.git_helper import clone

    with patch("builtins.input", return_value="y"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        clone("https://github.com/example/repo.git", "/tmp/test-repo")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "clone" in args


def test_SS_004_git_clone_skips_on_decline():
    """git clone does NOT execute when user declines."""
    from scripts.utils.git_helper import clone

    with patch("builtins.input", return_value="n"), \
         patch("subprocess.run") as mock_run:
        clone("https://github.com/example/repo.git", "/tmp/test-repo")
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# Crazyflie Configuration
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="requires hardware: Crazyflie connected via USB")
def test_SS_010():
    """There shall be a tool to write the radio address to the Crazyflie over USB."""


def test_SS_010_configure_crazyflie_script_exists():
    """configure_crazyflie.py exists and has a main() function."""
    path = os.path.join(_scripts_dir(), "configure_crazyflie.py")
    assert os.path.exists(path)

    import importlib.util
    spec = importlib.util.spec_from_file_location("configure_crazyflie", path)
    mod = importlib.util.module_from_spec(spec)
    # Don't exec (would try to import cflib); just check source
    with open(path) as f:
        src = f.read()
    assert "def main(" in src, "configure_crazyflie.py has no main() function"
    assert "radio_channel" in src or "radio_address" in src, (
        "configure_crazyflie.py does not configure radio settings"
    )


def test_SS_011_configure_uri_saves_to_correct_path():
    """There shall be a tool to configure the Crazyflie URI, stored in crazypilot_config.json."""
    path = os.path.join(_scripts_dir(), "configure_crazyflie.py")
    with open(path) as f:
        src = f.read()
    assert "crazypilot_config.json" in src, (
        "configure_crazyflie.py does not reference crazypilot_config.json"
    )
    assert "crazyflie_uri" in src, "configure_crazyflie.py does not store crazyflie_uri"


@pytest.mark.skip(reason="requires hardware: real Crazyflie with Crazyradio to test connection")
def test_SS_012():
    """There shall be a tool to verify that the configured Crazyflie URI is reachable."""


def test_SS_012_test_connection_script_exists():
    """test_connection.py exists and tests connectivity."""
    path = os.path.join(_scripts_dir(), "test_connection.py")
    assert os.path.exists(path)
    with open(path) as f:
        src = f.read()
    assert "def main(" in src
    # Should reference the config file
    assert "crazypilot_config.json" in src or "crazyflie_uri" in src


# ---------------------------------------------------------------------------
# Dependency Setup
# ---------------------------------------------------------------------------

def test_SS_015_setup_dependencies_script_exists():
    """There shall be a tool to install all software dependencies."""
    path = os.path.join(_scripts_dir(), "setup_dependencies.py")
    assert os.path.exists(path)
    with open(path) as f:
        src = f.read()
    assert "def main(" in src


@pytest.mark.skip(reason="requires hardware: actual apt-get and pip install on target system")
def test_SS_015_installs_all_deps():
    """Tool installs all required Python packages and system packages."""


def test_SS_015_references_requirements_txt():
    """setup_dependencies.py uses requirements.txt for Python packages."""
    path = os.path.join(_scripts_dir(), "setup_dependencies.py")
    with open(path) as f:
        src = f.read()
    assert "requirements.txt" in src, "setup_dependencies.py does not reference requirements.txt"


# ---------------------------------------------------------------------------
# Service Setup
# ---------------------------------------------------------------------------

def test_SS_020_setup_services_script_exists():
    """There shall be a tool to set up services for auto-starting Crazypilot on boot."""
    path = os.path.join(_scripts_dir(), "setup_services.py")
    assert os.path.exists(path)
    with open(path) as f:
        src = f.read()
    assert "def main(" in src


def test_SS_020_setup_services_uses_systemd():
    """setup_services.py sets up a systemd service for auto-start."""
    path = os.path.join(_scripts_dir(), "setup_services.py")
    with open(path) as f:
        src = f.read()
    assert "systemctl" in src, "setup_services.py does not use systemctl"
    assert "enable" in src, "setup_services.py does not enable the service"
    assert "crazypilot" in src, "setup_services.py does not reference crazypilot service"


@pytest.mark.skip(reason="requires hardware: real systemd on Raspberry Pi with sudo")
def test_SS_020_service_enables_on_boot():
    """Service is installed and enabled to auto-start on boot."""


def test_SS_020_service_unit_content():
    """The generated systemd service unit references the crazypilot binary."""
    import importlib.util
    scripts_dir = _scripts_dir()
    path = os.path.join(scripts_dir, "setup_services.py")

    with open(path) as f:
        src = f.read()

    # The service unit should exec crazypilot
    assert "crazypilot" in src
    assert "ExecStart" in src or "exec" in src.lower()


# ---------------------------------------------------------------------------
# Debugging Setup
# ---------------------------------------------------------------------------

def test_SS_030_setup_ssh_script_exists():
    """There shall be a tool to enable SSH access on the Raspberry Pi."""
    path = os.path.join(_scripts_dir(), "setup_ssh.py")
    assert os.path.exists(path)
    with open(path) as f:
        src = f.read()
    assert "def main(" in src


def test_SS_030_setup_ssh_enables_ssh():
    """setup_ssh.py enables and starts the SSH service."""
    path = os.path.join(_scripts_dir(), "setup_ssh.py")
    with open(path) as f:
        src = f.read()
    assert "ssh" in src.lower()
    assert "enable" in src
    assert "systemctl" in src


@pytest.mark.skip(reason="requires hardware: real Raspberry Pi with sudo and systemd")
def test_SS_030_ssh_actually_enabled():
    """SSH service is actually enabled and accessible on the Raspberry Pi."""
