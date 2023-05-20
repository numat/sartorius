"""Test the driver responds with correct data."""
from unittest import mock

import pytest

from sartorius import command_line
from sartorius.mock import Scale


@pytest.fixture()
def scale_driver():
    """Confirm the scale correctly initializes."""
    return Scale('fakeip')


@pytest.fixture()
def expected_response():
    """Return mocked scale data."""
    return {'model': 'SIWADCP-1-',
            'serial': '37454321',
            'software': '00-37-09'}


@mock.patch('sartorius.Scale', Scale)
def test_driver_cli(capsys):
    """Confirm the commandline interface works."""
    command_line(['fakeip'])
    captured = capsys.readouterr()
    assert '"stable": true' in captured.out


@pytest.mark.parametrize(('response', 'expected'),
                         #  KKKKKK+*AAAAAAAA*EEECRLF    mass   units  stable
                         [('N     +   0.1234 g  \r\n', (0.1234, 'g', True)),
                          ('N     +   9.9999 kg \r\n', (9.9999, 'kg', True)),
                          ('N     +   5.4321    \r\n', (5.4321, '', False))])
def test_parse(scale_driver, response, expected):
    """Test the response parsing code.

    Scale weight is returned according to the SMA communication standard:
    K K K K K K + * A A A A A A A A * E E E CR LF
    K: ID code character
    +: plus or minus
    *: space
    A: Digit or letter
    E: unit symbol
    """
    result = scale_driver._parse(response)

    assert result['mass'] == expected[0]
    assert result['units'] == expected[1]
    assert result['stable'] == expected[2]


async def test_get_response(scale_driver, expected_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_response == await scale_driver.get_info()


async def test_readme_example(expected_response):
    """Confirm the readme example using an async context manager works."""

    async def get():
        async with Scale('scale-ip.local') as scale:
            await scale.zero()             # Zero and tare the scale
            response = await scale.get()       # Get mass, units, stability
            assert response['stable'] is True
            assert expected_response == await scale.get_info()  # Get model, serial, software
    await get()
