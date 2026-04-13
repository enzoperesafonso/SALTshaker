"""
Specialized Observer for the Southern African Large Telescope (SALT).

This module provides the `SaltObserver` class, which extends the standard 
`astroplan.Observer` with SALT-specific tracking and planning capabilities.
"""

from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord
import astropy.units as u
from saltshaker.model import get_model
from functools import lru_cache

class SaltObserver(Observer):
    """
    A specialized Observer for SALT.
    
    This class inherits from `astroplan.Observer` and maintains SALT's 
    geographic location. It adds methods for calculating SALT-specific 
    visibility tracks and available track lengths using the 
    `SaltTrackingModel`.

    Attributes:
        tracking_model (SaltTrackingModel): The singleton instance of the 
            SALT tracking geometry model.
    """
    def __init__(self, **kwargs):
        """
        Initializes the SaltObserver.

        If location coordinates are not provided, it defaults to SALT's 
        geodetic location:
        - Longitude: 20° 48' 38.5" E
        - Latitude: 32° 22' 33.6" S
        - Height: 1798 m

        Args:
            **kwargs: Configuration arguments passed to `astroplan.Observer`.
        """
        if 'location' not in kwargs:
            kwargs['location'] = EarthLocation.from_geodetic(
                lon=20.8107 * u.deg,
                lat=-32.3760 * u.deg,
                height=1798 * u.m
            )
        if 'name' not in kwargs:
            kwargs['name'] = "SALT"
            
        super().__init__(**kwargs)
        self.tracking_model = get_model()

    def local_sidereal_time(self, time):
        """Cached version of local_sidereal_time (for scalars only)."""
        if hasattr(time, 'isscalar') and not time.isscalar:
            return super().local_sidereal_time(time)
        return self._local_sidereal_time_cached(time)

    @lru_cache(maxsize=128)
    def _local_sidereal_time_cached(self, time):
        """Internal cached method for scalar times."""
        return super().local_sidereal_time(time)

    def get_tracks(self, target, time):
        """
        Calculates all visibility windows for a target on a given date.
        
        This is a convenience wrapper for `saltshaker.planning.get_visibility_windows`.

        Args:
            target (SkyCoord): The celestial coordinates of the target.
            time (Time): The observation date. This typically represents 
                the noon-to-noon observing window.

        Returns:
            list[VisibilityWindow]: A list of objects representing the 
                time intervals when the target is observable.
        """
        from saltshaker.planning import get_visibility_windows
        return get_visibility_windows(target, time, observer=self)

    def track_length(self, target, time):
        """
        Returns the remaining track length for a target at a specific time.
        
        This is a convenience wrapper for `saltshaker.planning.get_track_length`.

        Args:
            target (SkyCoord): The celestial coordinates of the target.
            time (Time): The exact moment to check.

        Returns:
            Quantity: The available tracking duration in units of time (seconds).
        """
        from saltshaker.planning import get_track_length
        return get_track_length(target, time, observer=self)

_cached_observer = None

def get_salt_observer():
    """
    Factory function to get a pre-configured SaltObserver instance.
    Uses a cached singleton instance for performance.

    Returns:
        SaltObserver: An observer instance set to SALT's coordinates.
    """
    global _cached_observer
    if _cached_observer is None:
        _cached_observer = SaltObserver()
    return _cached_observer
