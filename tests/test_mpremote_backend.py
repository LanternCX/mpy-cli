"""mpremote backend tests."""

from pathlib import Path

from mpy_cli.backend.mpremote import MpremoteBackend


def test_upload_builds_expected_command() -> None:
    """@brief Upload command should match mpremote fs cp syntax."""
    backend = MpremoteBackend(binary="mpremote")

    cmd = backend.build_upload_command(
        port="/dev/ttyACM0",
        local=Path("main.py"),
        remote="main.py",
    )

    assert cmd == [
        "mpremote",
        "connect",
        "/dev/ttyACM0",
        "fs",
        "cp",
        "main.py",
        ":main.py",
    ]


def test_delete_builds_expected_command() -> None:
    """@brief Delete command should target remote path."""
    backend = MpremoteBackend(binary="mpremote")

    cmd = backend.build_delete_command(port="/dev/ttyACM0", remote="obsolete.py")

    assert cmd == [
        "mpremote",
        "connect",
        "/dev/ttyACM0",
        "fs",
        "rm",
        ":obsolete.py",
    ]
