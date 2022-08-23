"""Test the driver responds with correct data."""
from unittest import mock

import pytest

from sartorius import command_line
from sartorius.mock import Scale


@pytest.fixture
def scale_driver():
    """Confirm the scale correctly initializes."""
    return Scale('fakeip')


@pytest.fixture
def expected_response():
    """Return mocked scale data."""
    return {"model": "SIWADCP-1-",
            "serial": "37454321",
            "software": "00-37-09"}


@mock.patch('sartorius.Scale', Scale)
def test_driver_cli(capsys):
    """Confirm the commandline interface works."""
    command_line(['fakeip'])
    captured = capsys.readouterr()
    assert '"stable": true' in captured.out


async def test_get_response(scale_driver, expected_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_response == await scale_driver.get_info()
