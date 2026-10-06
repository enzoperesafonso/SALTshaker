
import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.time import Time

from saltshaker import (
    VisibilityWindow,
    get_salt_observer,
    get_tracks,
    get_visibility_windows,
    visibility_table,
)


def test_get_tracks_sirius(sirius):
    """
    Tests the get_tracks function with the coordinates of Sirius.
    Sirius is a known bright star, and its visibility from SALT is well-understood.
    This test verifies that the function returns a reasonable track length.
    """
    # Coordinates of Sirius

    # A date for the observation
    obs_date = '2026-01-15'

    # Get the visibility windows
    windows = get_visibility_windows(sirius, obs_date)

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

def test_target_never_visible(polaris):
    """
    Tests with a target that is never visible from SALT (e.g., Polaris).
    """
    obs_date = '2026-01-15'

    windows = get_visibility_windows(polaris, obs_date)

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

    windows = get_visibility_windows(SkyCoord(ra=180*u.deg, dec=dec_split*u.deg), obs_date)

    # This should result in two visibility windows (East and West)
    assert len(windows) == 2
    assert isinstance(windows[0], VisibilityWindow)
    assert isinstance(windows[1], VisibilityWindow)

    # The first window should be the eastern track (rising)
    # The second window should be the western track (setting)
    # We can check this by looking at the start times.
    # A more robust check would be to convert times back to HA.
    assert windows[0].start_time_utc < windows[1].start_time_utc


def test_get_tracks_is_deprecated():
    with pytest.warns(DeprecationWarning):
        assert get_tracks(-15.0, '2026-01-15')


def test_time_and_string_dates_agree():
    """A date string means noon UTC; a Time is used as given."""
    coord = SkyCoord(ra=100 * u.deg, dec=-30 * u.deg)
    from_str = get_visibility_windows(coord, '2026-01-15')
    from_time = get_visibility_windows(coord, Time('2026-01-15 12:00:00'))
    from_str_time = get_visibility_windows(coord, '2026-01-15 12:00:00')
    assert len(from_str) == len(from_time) == len(from_str_time)
    for a, b in zip(from_str, from_time):
        assert abs((a.start_time - b.start_time).sec) < 1e-6


def test_windows_stay_inside_period():
    coord = SkyCoord(ra=np.linspace(0, 350, 15) * u.deg, dec=np.full(15, -30.0) * u.deg)
    start = Time('2026-01-15 12:00:00')
    for windows in get_visibility_windows(coord, start):
        for w in windows:
            assert w.start_time >= start and w.end_time <= start + 24 * u.hour
            assert w.duration > 0


def test_night_only_windows_are_dark():
    observer = get_salt_observer()
    coord = SkyCoord(ra=100 * u.deg, dec=-30 * u.deg)
    all_windows = get_visibility_windows(coord, '2026-01-15')
    night = get_visibility_windows(coord, '2026-01-15', night_only=True)
    assert sum(w.duration for w in night) <= sum(w.duration for w in all_windows)
    for w in night:
        mid = w.start_time + (w.end_time - w.start_time) / 2
        assert observer.is_night(mid, horizon=-18 * u.deg)


def test_visibility_table():
    coords = SkyCoord(ra=[10, 20, 30] * u.deg, dec=[-30, -40, 50] * u.deg)
    table = visibility_table(coords, '2026-03-01', names=['a', 'b', 'c'])
    assert set(table['name']) <= {'a', 'b'}   # 'c' (Dec +50) is never observable
    assert 'c' not in set(table['name'])
    assert len(table) >= 2


def test_string_and_fixedtarget_inputs():
    from astroplan import FixedTarget
    coord = SkyCoord(ra=100 * u.deg, dec=-30 * u.deg)
    ft = FixedTarget(coord=coord, name='x')
    assert len(get_visibility_windows(ft, '2026-01-15')) == len(get_visibility_windows(coord, '2026-01-15'))
    with pytest.raises(TypeError):
        get_visibility_windows(42, '2026-01-15')
