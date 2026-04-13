import pytest
from saltshaker.observer import get_salt_observer
from saltshaker.planning import get_visibility_windows
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
import numpy as np

def test_vectorized_visibility_windows():
    """Tests that get_visibility_windows handles multiple targets correctly."""
    observer = get_salt_observer()
    
    # 3 targets
    targets = SkyCoord(
        ra=[10, 20, 30] * u.deg,
        dec=[-30, -40, -50] * u.deg
    )
    obs_date = '2026-03-01'
    
    # Scalar calls in a loop
    scalar_results = []
    for target in targets:
        scalar_results.append(get_visibility_windows(target, obs_date, observer=observer))
        
    # Vectorized call
    vector_results = get_visibility_windows(targets, obs_date, observer=observer)
    
    assert len(vector_results) == len(targets)
    for i in range(len(targets)):
        assert len(vector_results[i]) == len(scalar_results[i])
        for j in range(len(vector_results[i])):
            # Compare start times
            assert (vector_results[i][j].start_time - scalar_results[i][j].start_time).sec < 1e-3
            # Compare durations
            assert abs(vector_results[i][j].duration - scalar_results[i][j].duration) < 1e-3
