"""
SALT-specific observation constraints for astroplan.

This module provides constraint classes that integrate with the `astroplan` 
scheduling ecosystem to enforce SALT's unique tracking and lunar limits.
"""

from astroplan import Constraint
import astropy.units as u
from saltshaker.model import get_model
import numpy as np

class SaltTrackLengthConstraint(Constraint):
    """
    Constraint on the remaining track length of a target.
    
    This constraint ensures that at any given time, the target has a 
    remaining track length of at least `min_track_length`. This is 
    essential for scheduling exposures that must not be interrupted by 
    the tracker reaching its physical limit.

    Attributes:
        min_track_length (Quantity): The minimum required track duration.
        tracking_model (SaltTrackingModel): The singleton model used for 
            calculations.
    """
    def __init__(self, min_track_length=None):
        """
        Initializes the SaltTrackLengthConstraint.

        Args:
            min_track_length (Quantity | None): The minimum duration needed. 
                Defaults to 0 seconds.
        """
        self.min_track_length = min_track_length if min_track_length is not None else 0 * u.second
        self.tracking_model = get_model()

    def compute_constraint(self, times, observer, targets):
        """
        Evaluates the constraint for a set of times and targets.
        
        This implementation is fully vectorized for maximum performance.
        """
        if times.isscalar:
            times_arr = times[None]
        else:
            times_arr = times
            
        # 1. Calculate LST for all times (Astroplan does this efficiently)
        lst = observer.local_sidereal_time(times_arr)
        
        # 2. Initialize result array (n_targets x n_times)
        constraint_result = np.zeros((len(targets), len(times_arr)), dtype=bool)
        
        for i, target in enumerate(targets):
            declination = target.dec.to(u.deg).value
            ra = target.ra

            
            # 3. Calculate all hour angles at once (Vectorized)
            ha = (lst - ra).to(u.hourangle).value
            
            # 4. Normalize HAs to [-12, 12] range (Vectorized)
            ha[ha > 12] -= 24
            ha[ha < -12] += 24
            
            # 5. Get all track lengths at once (Vectorized call to optimized model)
            track_lens = self.tracking_model.track_length(declination, ha) * u.second
            
            # 6. Apply constraint (Vectorized)
            constraint_result[i] = track_lens >= self.min_track_length
                
        return constraint_result

class SaltMoonConstraint(Constraint):
    """
    Constraint on Moon phase and position.
    
    This constraint is satisfied if:

    1. The Moon's illuminated fraction is less than or equal to 
       `max_illumination`.
    2. OR, the Moon is currently below the horizon.

    Attributes:
        max_illumination (float): Maximum allowed illuminated fraction (0 to 1).
    """
    def __init__(self, max_illumination=1.0):
        """
        Initializes the SaltMoonConstraint.

        Args:
            max_illumination (float): Maximum illuminated fraction. 
                Defaults to 1.0 (no constraint).
        """
        self.max_illumination = max_illumination

    def compute_constraint(self, times, observer, targets):
        """
        Evaluates the constraint for a set of times and targets.
        """
        if times.isscalar:
            times_arr = times[None]
        else:
            times_arr = times

        from astroplan import moon_illumination
        illum = moon_illumination(times_arr)
        illum_ok = illum <= self.max_illumination
        
        moon_altaz = observer.moon_altaz(times_arr)
        moon_down = moon_altaz.alt <= 0 * u.deg
        
        # The constraint is satisfied if:
        # (Moon illumination <= max) OR (Moon is below horizon)
        satisfied_global = np.logical_or(illum_ok, moon_down)
        
        # Expand to (n_targets x n_times)
        return np.tile(satisfied_global, (len(targets), 1))
