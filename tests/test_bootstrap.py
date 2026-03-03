"""Bootstrap tests for package skeleton."""

from pathlib import Path


def test_package_has_version() -> None:
    """@brief Verify package exposes a non-empty version string."""
    from mpy_cli import __version__

    assert isinstance(__version__, str)
    assert __version__


def test_module_entrypoint_exists() -> None:
    """@brief Verify module entrypoint file exists."""
    assert Path("mpy_cli/__main__.py").exists()
