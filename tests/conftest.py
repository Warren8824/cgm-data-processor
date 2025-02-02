"""Global test fixtures."""

import pytest


@pytest.fixture
def mock_logger(mocker):
    """Mock the format registry logger."""
    return mocker.patch("src.core.format_registry.logger")


@pytest.fixture
def device_dir(tmp_path):
    """Create temporary devices directory."""
    devices_dir = tmp_path / "devices"
    devices_dir.mkdir()
    return devices_dir
