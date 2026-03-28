
import pytest
from saltshaker import get_tracks, VisibilityWindow
from astropy.coordinates import SkyCoord
import astropy.units as u

def test_get_tracks_sirius():
    """
    Tests the get_tracks function with the coordinates of Sirius.
    Sirius is a known bright star, and its visibility from SALT is well-understood.
    This test verifies that the function returns a reasonable track length.
    """
    # Coordinates of Sirius
    sirius = SkyCoord.from_name('Sirius')
    sirius_dec = sirius.dec.deg

    # A date for the observation
    obs_date = '2026-01-15'

    # Get the visibility windows
    windows = get_tracks(sirius_dec, obs_date)

    # Sirius should be visible from SALT.
    # It is far enough south that it should have a single, long track.
    assert windows is not None
    assert isinstance(windows, list)
    assert len(windows) > 0
    
    # Check the type of the returned items
    for window in windows:
        assert isinstance(window, VisibilityWindow)

    # Sum the duration of all windows
    total_duration = sum(w.duration for w in windows)

    # Based on the SALT data file, the track length for Sirius is around 2.1 hours.
    # We will check if the returned duration is within a reasonable range.
    # 2.1 hours = 7560 seconds. Let's give it a tolerance.
    assert 7000 < total_duration < 8500

def test_target_never_visible():
    """
    Tests with a target that is never visible from SALT (e.g., Polaris).
    """
    polaris = SkyCoord.from_name('Polaris')
    polaris_dec = polaris.dec.deg

    obs_date = '2026-01-15'

    windows = get_tracks(polaris_dec, obs_date)

    assert windows == []

def test_split_track():
    """
    Tests with a target that should have a split track.
    A target with a declination around -15 degrees should pass through the
    zenith dead zone of SALT.
    """
    # A declination that is expected to have a split track
    dec_split = -15.0

    obs_date = '2026-01-15'

    windows = get_tracks(dec_split, obs_date)

    # This should result in two visibility windows (East and West)
    assert len(windows) == 2
    assert isinstance(windows[0], VisibilityWindow)
    assert isinstance(windows[1], VisibilityWindow)

    # The first window should be the eastern track (rising)
    # The second window should be the western track (setting)
    # We can check this by looking at the start times.
    # A more robust check would be to convert times back to HA.
    assert windows[0].start_time_utc < windows[1].start_time_utc
