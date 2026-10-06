import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.time import Time

from saltshaker import SaltMoonConstraint, SaltTrackLengthConstraint, get_salt_observer


def test_track_length_constraint(sirius):
    """Tests the SaltTrackLengthConstraint."""
    observer = get_salt_observer()
    target = sirius
    
    # Sirius transits around 23:30 UT on Jan 15th
    # But SALT has a zenith hole!
    # Let's pick a time in the East track (approx 19:00 UT)
    time = Time('2026-01-15 19:00:00')
    
    # Should have at least 1000s track length
    constraint = SaltTrackLengthConstraint(min_track_length=1000 * u.second)
    res = constraint.compute_constraint(time, observer, [target])
    assert res[0][0] == True
    
    # Should NOT have 5000s track length (max is ~3800s)
    constraint = SaltTrackLengthConstraint(min_track_length=5000 * u.second)
    res = constraint.compute_constraint(time, observer, [target])
    assert res[0][0] == False

def test_moon_constraint(sirius):
    """Tests the SaltMoonConstraint."""
    observer = get_salt_observer()
    target = sirius
    
    # Jan 15th 2026 is near New Moon (Phase ~ 0.04)
    time = Time('2026-01-15 00:00:00')
    
    # 0.5 max illumination should pass
    constraint = SaltMoonConstraint(max_illumination=0.5)
    res = constraint.compute_constraint(time, observer, [target])
    assert res[0][0] == True
    
    # Wait! Jan 15th 2026.
    # New Moon is on Jan 18th 2026.
    # So on Jan 15th it's a thin crescent.
    
    # Full Moon (Jan 3-4 2026) rises around sunset, so 18:00 UTC (20:00 local)
    # is well after moonrise and the Moon is up.
    time_full = Time('2026-01-03 20:00:00')
    assert observer.moon_altaz(time_full).alt > 0 * u.deg
    constraint = SaltMoonConstraint(max_illumination=0.1)
    res = constraint.compute_constraint(time_full, observer, [target])
    assert res[0][0] == False


def test_constraints_array_times_and_targets(sirius):
    """Both constraints accept arrays of times and several targets."""
    observer = get_salt_observer()
    targets = [sirius, SkyCoord(ra=10 * u.deg, dec=-40 * u.deg)]
    times = Time('2026-01-15 12:00:00') + np.arange(0, 24, 2) * u.hour
    for constraint in (SaltTrackLengthConstraint(min_track_length=600 * u.second),
                       SaltMoonConstraint(max_illumination=0.5)):
        res = constraint.compute_constraint(times, observer, targets)
        assert res.shape == (2, len(times))
