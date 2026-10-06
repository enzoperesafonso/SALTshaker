import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord


@pytest.fixture(scope="session")
def sirius():
    """Sirius (ICRS), hardcoded so tests never need network access."""
    return SkyCoord(ra=101.28715533 * u.deg, dec=-16.71611586 * u.deg)


@pytest.fixture(scope="session")
def polaris():
    return SkyCoord(ra=37.95456067 * u.deg, dec=89.26410897 * u.deg)
