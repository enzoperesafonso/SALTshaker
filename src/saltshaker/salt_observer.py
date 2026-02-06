from astroplan import Observer
from astropy.coordinates import EarthLocation
import astropy.units as u

def SaltObserver():
    """
    Returns a pre-configured astroplan.Observer for the Southern African
    Large Telescope (SALT).

    The official observatory code is B31.

    Returns:
        astroplan.Observer: Observer object for SALT.
    """
    salt_location = EarthLocation.from_geodetic(
        lon=20.8107 * u.deg,
        lat=-32.3760 * u.deg,
        height=1798 * u.m
    )
    return Observer(name="SALT", location=salt_location)
