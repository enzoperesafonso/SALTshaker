"""
Observation planning and scheduling utilities for SALT.

This module provides the core functional API for determining when targets 
are visible at SALT and managing observing semesters. 

It handles the conversion of theoretical tracking limits into actual 
Universal Time (UTC) windows and provides night-by-night semester 
iterators.
"""

from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
from saltshaker.model import get_model
import numpy as np

class VisibilityWindow:
    """
    Represents a specific time interval when a target is visible at SALT.

    Attributes:
        start_time (Time): The exact beginning of the visibility window.
        end_time (Time): The exact end of the visibility window.
        duration (float): The total duration of the window in seconds.
    """
    def __init__(self, start_time, end_time):
        """
        Initializes the visibility window.

        Args:
            start_time (Time): Start of the observable period.
            end_time (Time): End of the observable period.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.duration = (end_time - start_time).to(u.second).value

    @property
    def start_time_utc(self):
        """Returns the start time as a UTC ISO string (e.g., '2026-01-15 18:30:00')."""
        return self.start_time.utc.iso

    @property
    def end_time_utc(self):
        """Returns the end time as a UTC ISO string."""
        return self.end_time.utc.iso
    
    def __repr__(self):
        return f"<VisibilityWindow {self.start_time_utc} to {self.end_time_utc} ({self.duration:.1f}s)>"

def get_visibility_windows(target_coord, obs_date, observer=None):
    """
    Calculates the observable UTC windows for a target on a specific date.

    This function converts tracking hour angle limits into a sequence of 
    UTC time intervals. For many declinations, this will return two 
    windows (an Eastern rising track and a Western setting track).

    Args:
        target_coord (SkyCoord): The celestial coordinates of the target.
        obs_date (str | Time): The date of observation. If a string is 
            provided (e.g., '2026-01-15'), the 24-hour window starts 
            at 12:00:00 UTC on that day.
        observer (SaltObserver | None): The observer instance to use for 
            LST and coordinate calculations. Defaults to a standard 
            `SaltObserver`.

    Returns:
        list[VisibilityWindow]: A list of visibility windows, sorted 
            chronologically. Returns an empty list if the target never 
            enters the tracking zone.
    """
    if observer is None:
        from saltshaker.observer import get_salt_observer
        observer = get_salt_observer()
        
    tracking_model = get_model()
    declination = target_coord.dec.deg
    
    # Define the observation time range (24 hours starting from noon)
    if isinstance(obs_date, str):
        start_time = Time(f"{obs_date} 12:00:00")
    else:
        start_time = obs_date
        
    end_time = start_time + 24 * u.hour
    
    try:
        east_track_ha = tracking_model.get_east_track(declination)
        west_track_ha = tracking_model.get_west_track(declination)
    except ValueError:
        return []
        
    # LST at start_time
    lst_start = observer.local_sidereal_time(start_time).hour
    
    # Target HA at start_time
    target_ra_hours = target_coord.ra.hour
    start_ha = lst_start - target_ra_hours
    # Normalize to [-12, 12]
    if start_ha >= 12: start_ha -= 24
    if start_ha < -12: start_ha += 24

    tracks = []
    SIDEREAL_TO_SOLAR = 1.0 / 1.00273790935

    def calculate_track_ut(track_ha_limits):
        if track_ha_limits is None:
            return
        
        ha_start, ha_end = track_ha_limits
        diff_start = ha_start - start_ha
        diff_end = ha_end - start_ha
        
        # Shift forward if track has already passed
        if diff_start < 0 and diff_end < 0:
            diff_start += 24
            diff_end += 24
            
        t_start = start_time + (diff_start * SIDEREAL_TO_SOLAR) * u.hour
        t_end = start_time + (diff_end * SIDEREAL_TO_SOLAR) * u.hour
        
        overlap_start = max(start_time, t_start)
        overlap_end = min(end_time, t_end)
        
        if overlap_start < overlap_end:
            tracks.append(VisibilityWindow(overlap_start, overlap_end))

    calculate_track_ut(east_track_ha)
    calculate_track_ut(west_track_ha)
        
    tracks.sort(key=lambda x: x.start_time)
    return tracks

def get_track_length(target, time, observer=None):
    """
    Returns the available track length for a target at a specific moment.

    The "Track Length" is the remaining duration (in seconds) that the 
    tracker can follow the object before reaching its physical limit. 
    This is highly dependent on both declination and the target's 
    current position in the tracking zone (hour angle).

    Args:
        target (SkyCoord): The celestial coordinates of the target.
        time (Time): The exact moment of observation.
        observer (SaltObserver | None): The observer instance to use. 
            Defaults to a standard `SaltObserver`.

    Returns:
        Quantity: The remaining tracking duration in units of time (seconds).
    """
    if observer is None:
        from saltshaker.observer import get_salt_observer
        observer = get_salt_observer()
        
    tracking_model = get_model()
    lst = observer.local_sidereal_time(time)
    ha = (lst - target.ra).to(u.hourangle).value
    
    # Normalize HA to [-12, 12]
    if ha > 12: ha -= 24
    elif ha < -12: ha += 24
        
    return tracking_model.track_length(target.dec.deg, ha) * u.second

def is_target_observable(target):
    """
    Checks if a target is EVER observable from SALT based on its declination.

    SALT's fixed-altitude design limits visibility to a specific range 
    of declinations (approximately -75° to +10°). This function returns 
    True if the target's declination ever enters SALT's tracking annulus.

    Args:
        target (SkyCoord | float): The target to check. Can be an 
            astropy `SkyCoord` object or a float representing the 
            declination in degrees.

    Returns:
        bool: True if the target is observable, False otherwise.
    """
    if isinstance(target, (float, int, np.float64)):
        dec = target
    else:
        dec = target.dec.deg
        
    tracking_model = get_model()
    return tracking_model.get_max_track_length(dec) > 0

def get_tracks(target_coord, obs_date):
    """
    Compatibility wrapper for `get_visibility_windows`.
    
    Deprecated: Use `get_visibility_windows` instead.

    Args:
        target_coord (SkyCoord | float): Target coordinate or declination.
        obs_date (str | Time): Date of observation.

    Returns:
        list[VisibilityWindow]: Observable time windows.
    """
    if isinstance(target_coord, (float, int, np.float64)):
        target_coord = SkyCoord(ra=0*u.deg, dec=target_coord*u.deg)
    return get_visibility_windows(target_coord, obs_date)

def get_semester_start(year, semester):
    """
    Returns the official start date of a SALT observing semester.
    
    - Semester 1 (e.g., 2026-1) starts March 1st.
    - Semester 2 (e.g., 2026-2) starts October 1st.

    Args:
        year (int): The calendar year.
        semester (int): The semester number (1 or 2).

    Returns:
        Time: Start of the semester (12:00:00 UTC).
    """
    if semester == 1:
        return Time(f"{year}-03-01 12:00:00")
    elif semester == 2:
        return Time(f"{year}-10-01 12:00:00")
    else:
        raise ValueError("Semester must be 1 or 2")

def get_semester_end(year, semester):
    """
    Returns the official end date of a SALT observing semester.

    Args:
        year (int): The calendar year.
        semester (int): The semester number (1 or 2).

    Returns:
        Time: End of the semester (12:00:00 UTC).
    """
    if semester == 1:
        return Time(f"{year}-10-01 12:00:00")
    elif semester == 2:
        return Time(f"{year+1}-03-01 12:00:00")
    else:
        raise ValueError("Semester must be 1 or 2")

def get_semester_nights(year, semester, observer=None):
    """
    Generates a sequence of observing nights for an entire semester.

    A "night" is defined as the period between evening astronomical 
    twilight (-18° altitude) and morning astronomical twilight.

    Args:
        year (int): The calendar year.
        semester (int): The semester number (1 or 2).
        observer (SaltObserver | None): The observer instance to use 
            for twilight calculations. Defaults to a standard 
            `SaltObserver`.

    Returns:
        list[tuple[Time, Time]]: A list of tuples, where each tuple is 
            (evening_twilight, morning_twilight).
    """
    if observer is None:
        from saltshaker.observer import get_salt_observer
        observer = get_salt_observer()
        
    start_time = get_semester_start(year, semester)
    end_time = get_semester_end(year, semester)
    
    nights = []
    current_time = start_time
    
    while current_time < end_time:
        try:
            evening_twilight = observer.twilight_evening_astronomical(current_time, which='next')
            morning_twilight = observer.twilight_morning_astronomical(evening_twilight, which='next')
            
            if evening_twilight < end_time:
                nights.append((evening_twilight, morning_twilight))
        except:
            # Handle locations where twilight might not occur
            pass
        current_time += 1 * u.day
        
    return nights
