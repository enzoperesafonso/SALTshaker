import pytest
from saltshaker import get_salt_observer, SaltTrackLengthConstraint, SaltMoonConstraint
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

def test_track_length_constraint():
    """Tests the SaltTrackLengthConstraint."""
    observer = get_salt_observer()
    target = SkyCoord.from_name('Sirius')
    
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

def test_moon_constraint():
    """Tests the SaltMoonConstraint."""
    observer = get_salt_observer()
    target = SkyCoord.from_name('Sirius')
    
    # Jan 15th 2026 is near New Moon (Phase ~ 0.04)
    time = Time('2026-01-15 00:00:00')
    
    # 0.5 max illumination should pass
    constraint = SaltMoonConstraint(max_illumination=0.5)
    res = constraint.compute_constraint(time, observer, [target])
    assert res[0][0] == True
    
    # Wait! Jan 15th 2026.
    # New Moon is on Jan 18th 2026.
    # So on Jan 15th it's a thin crescent.
    
    # Now check with Full Moon (approx Jan 4th 2026)
    time_full = Time('2026-01-04 00:00:00')
    # 0.1 max illumination should fail (unless Moon is down)
    constraint = SaltMoonConstraint(max_illumination=0.1)
    
    # We need to make sure the Moon is up to fail.
    # Check Moon altitude at that time.
    moon_altaz = observer.moon_altaz(time_full)
    if moon_altaz.alt > 0:
        res = constraint.compute_constraint(time_full, observer, [target])
        assert res[0][0] == False
