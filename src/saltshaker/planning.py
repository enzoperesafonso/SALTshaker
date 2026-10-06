"""
Observation planning and scheduling utilities for SALT.

This module provides the core functional API for determining when targets 
are visible at SALT and managing observing semesters. 

It handles the conversion of theoretical tracking limits into actual 
Universal Time (UTC) windows and provides night-by-night semester 
iterators.
"""

import warnings

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, SkyCoord, get_sun
from astropy.time import Time

from saltshaker.model import get_model

SIDEREAL_TO_SOLAR = 1.0 / 1.00273790935


def _as_skycoord(target):
    """
    Coerces a target-like object to a `SkyCoord`.

    Accepts a `SkyCoord`, an `astroplan.FixedTarget` (anything with a
    ``coord`` attribute) or a string name resolved with
    `SkyCoord.from_name` (requires network access).
    """
    if isinstance(target, SkyCoord):
        return target
    if isinstance(target, str):
        return SkyCoord.from_name(target)
    if hasattr(target, "coord"):
        return target.coord
    raise TypeError(f"Cannot interpret {type(target).__name__} as a target; "
                    "pass a SkyCoord, a FixedTarget or a resolvable name.")


def _resolve_start_time(obs_date):
    """
    Returns the start of the 24-hour search window.

    A date-only string ('2026-01-15') starts at 12:00:00 UTC on that day. A
    string containing a time, or a `Time`, is used exactly as given.
    """
    if isinstance(obs_date, str):
        text = obs_date.strip()
        if len(text) <= 10 and ":" not in text:
            text = f"{text} 12:00:00"
        return Time(text)
    return obs_date


def _night_intervals(observer, start_time, end_time):
    """Astronomical-night intervals (as Time pairs) overlapping [start, end]."""
    morn1 = observer.twilight_morning_astronomical(start_time, which="next")
    eve1 = observer.twilight_evening_astronomical(morn1, which="previous")
    intervals = [(max(eve1, start_time), min(morn1, end_time))]
    eve2 = observer.twilight_evening_astronomical(morn1, which="next")
    if eve2 < end_time:
        morn2 = observer.twilight_morning_astronomical(eve2, which="next")
        intervals.append((eve2, min(morn2, end_time)))
    return [(a, b) for a, b in intervals if a < b]


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
    
    @property
    def duration_quantity(self):
        """The window duration as an astropy `Quantity` (seconds)."""
        return self.duration * u.second

    def __iter__(self):
        """Allows ``start, end = window``."""
        return iter((self.start_time, self.end_time))

    def __repr__(self):
        return f"<VisibilityWindow {self.start_time_utc} to {self.end_time_utc} ({self.duration:.1f}s)>"

def get_visibility_windows(target_coord, obs_date, observer=None, night_only=False):
    """
    Calculates the observable UTC windows for a target (or targets) on a specific date.

    This function converts tracking hour angle limits into a sequence of 
    UTC time intervals. For many declinations, this will return two 
    windows (an Eastern rising track and a Western setting track).

    The search covers exactly 24 hours from the start time, so a track that 
    straddles the start or end of that period is truncated to it. These 
    windows are purely geometric (target inside SALT's tracking range) and 
    include daytime unless ``night_only=True``.

    Args:
        target_coord (SkyCoord | FixedTarget | str): The target(s). A string
            is resolved by name (requires network access).
        obs_date (str | Time): Start of the 24-hour search period. A 
            date-only string (e.g. '2026-01-15') starts at 12:00:00 UTC on 
            that day; a string with a time, or a `Time`, is used as given.
        observer (SaltObserver | None): The observer instance to use for 
            LST and coordinate calculations. Defaults to a standard 
            `SaltObserver`.
        night_only (bool): If True, windows are clipped to astronomical 
            night (Sun below -18 degrees).

    Returns:
        list[VisibilityWindow] | list[list[VisibilityWindow]]: A list of 
            visibility windows (for a single target) or a list of lists 
            (for multiple targets). Targets that are never observable give 
            an empty list.
    """
    if observer is None:
        from saltshaker.observer import get_salt_observer
        observer = get_salt_observer()
        
    tracking_model = get_model()
    target_coord = _as_skycoord(target_coord)
    
    # Handle both scalar and array targets
    is_scalar = target_coord.isscalar
    decls = target_coord.dec.deg
    ras = target_coord.ra.hour
    
    start_time = _resolve_start_time(obs_date)
    end_time = start_time + 24 * u.hour
    
    try:
        east_tracks = tracking_model.get_east_track(decls)
        west_tracks = tracking_model.get_west_track(decls)
    except ValueError:
        return [] if is_scalar else [[] for _ in range(len(target_coord))]
        
    lst_start = observer.local_sidereal_time(start_time).hour
    
    # Target HAs at start_time, normalized to [-12, 12)
    start_has = (lst_start - ras + 12) % 24 - 12

    night = _night_intervals(observer, start_time, end_time) if night_only else None

    def _get_windows_for_target(e_track, w_track, s_ha):
        tracks = []
        for track_ha_limits in [e_track, w_track]:
            if track_ha_limits is None or np.any(np.isnan(track_ha_limits)):
                continue
            
            ha_start, ha_end = track_ha_limits
            # A track recurs every sidereal day; consider the neighbouring
            # repeats so tracks near either edge of the period are not lost.
            for shift in (-24, 0, 24):
                diff_start = ha_start - s_ha + shift
                diff_end = ha_end - s_ha + shift
                t_start = start_time + (diff_start * SIDEREAL_TO_SOLAR) * u.hour
                t_end = start_time + (diff_end * SIDEREAL_TO_SOLAR) * u.hour

                spans = [(start_time, end_time)] if night is None else night
                for lo, hi in spans:
                    overlap_start = max(lo, t_start)
                    overlap_end = min(hi, t_end)
                    if overlap_start < overlap_end:
                        tracks.append(VisibilityWindow(overlap_start, overlap_end))
        
        tracks.sort(key=lambda x: x.start_time)
        return tracks

    if is_scalar:
        return _get_windows_for_target(east_tracks, west_tracks, start_has)

    # For arrays, east_tracks and west_tracks are tuples of arrays
    e_starts, e_ends = east_tracks
    w_starts, w_ends = west_tracks

    results = []
    for i in range(len(target_coord)):
        e = (e_starts[i], e_ends[i])
        w = (w_starts[i], w_ends[i]) if not np.isnan(w_starts[i]) else None
        results.append(_get_windows_for_target(e, w, start_has[i]))
    return results


def visibility_table(targets, obs_date, names=None, observer=None, night_only=False):
    """
    Builds an `astropy.table.Table` of visibility windows for many targets.

    Handy for screening a catalog: one row per window with the target name, 
    coordinates, UTC start/end and duration.

    Args:
        targets (SkyCoord): Array of target coordinates.
        obs_date (str | Time): See `get_visibility_windows`.
        names (list[str] | None): Target labels. Defaults to the row index.
        observer (SaltObserver | None): Observer to use.
        night_only (bool): Clip windows to astronomical night.

    Returns:
        astropy.table.Table: Columns ``name, ra, dec, start_utc, end_utc, 
            duration``. Targets with no windows contribute no rows.
    """
    from astropy.table import Table

    targets = _as_skycoord(targets)
    if targets.isscalar:
        targets = targets.reshape(1)
    if names is None:
        names = [str(i) for i in range(len(targets))]
    all_windows = get_visibility_windows(targets, obs_date, observer=observer,
                                         night_only=night_only)
    rows = []
    for name, coord, windows in zip(names, targets, all_windows):
        for w in windows:
            rows.append((name, coord.ra.deg, coord.dec.deg,
                         w.start_time.utc.strftime('%Y-%m-%d %H:%M:%S'),
                         w.end_time.utc.strftime('%Y-%m-%d %H:%M:%S'), round(w.duration, 1)))
    table = Table(rows=rows, names=("name", "ra", "dec", "start_utc", "end_utc", "duration"),
                  dtype=("U64", float, float, "U32", "U32", float))
    table["ra"].unit = u.deg
    table["dec"].unit = u.deg
    table["duration"].unit = u.s
    return table


def get_track_length(target, time, observer=None):
    """
    Returns the available track length for a target at a specific moment.

    The "Track Length" is the remaining duration (in seconds) that the 
    tracker can follow the object before reaching its physical limit. 
    This is highly dependent on both declination and the target's 
    current position in the tracking zone (hour angle).

    Args:
        target (SkyCoord | FixedTarget | str): The target(s).
        time (Time): The exact moment(s) of observation; scalar or array.
        observer (SaltObserver | None): The observer instance to use. 
            Defaults to a standard `SaltObserver`.

    Returns:
        Quantity: The remaining tracking duration in seconds. The shape 
            follows the broadcast of `target` and `time`.
    """
    if observer is None:
        from saltshaker.observer import get_salt_observer
        observer = get_salt_observer()
        
    target = _as_skycoord(target)
    tracking_model = get_model()
    lst = observer.local_sidereal_time(time)
    ha = (lst - target.ra).to(u.hourangle).value

    # Normalize HA to [-12, 12)
    ha = (ha + 12) % 24 - 12

    return tracking_model.track_length(target.dec.deg, ha) * u.second

def is_target_observable(target):
    """
    Checks if a target is EVER observable from SALT based on its declination.

    SALT's fixed-altitude design limits visibility to a specific range
    of declinations (the model covers -76 to +11.25 degrees). This 
    function returns True if the target's declination lies in that range.

    Args:
        target (SkyCoord | FixedTarget | str | Quantity | float | array-like): 
            The target(s) to check, or the declination(s) in degrees.

    Returns:
        bool | np.ndarray: True if the target is observable, False otherwise.
    """
    if isinstance(target, str) or hasattr(target, "coord"):
        target = _as_skycoord(target)
    if isinstance(target, SkyCoord):
        dec = target.dec.deg
    elif isinstance(target, u.Quantity):
        dec = target.to_value(u.deg)
    else:
        dec = np.asarray(target, dtype=float)

    lo, hi = get_model().dec_range
    result = (np.asarray(dec) >= lo) & (np.asarray(dec) <= hi)
    return bool(result) if result.ndim == 0 else result

def get_tracks(target_coord, obs_date, observer=None):
    """
    Compatibility wrapper for `get_visibility_windows`.
    
    Deprecated: Use `get_visibility_windows` instead.

    Args:
        target_coord (SkyCoord | float): Target coordinate or declination.
        obs_date (str | Time): Date of observation.
        observer (SaltObserver | None): Observer to use.

    Returns:
        list[VisibilityWindow]: Observable time windows.
    """
    warnings.warn("get_tracks is deprecated; use get_visibility_windows instead.",
                  DeprecationWarning, stacklevel=2)
    if isinstance(target_coord, (float, int, np.floating)):
        target_coord = SkyCoord(ra=0*u.deg, dec=target_coord*u.deg)
    return get_visibility_windows(target_coord, obs_date, observer=observer)

def _check_semester(semester):
    if semester not in (1, 2):
        raise ValueError("Semester must be 1 or 2")


def get_semester_start(year, semester):
    """
    Returns the start date of a SALT observing semester.
    
    - Semester 1 (e.g., 2026-1) starts May 1st.
    - Semester 2 (e.g., 2026-2) starts November 1st.

    Args:
        year (int): The calendar year.
        semester (int): The semester number (1 or 2).

    Returns:
        Time: Start of the semester (12:00:00 UTC).
    """
    _check_semester(semester)
    return Time(f"{year}-05-01 12:00:00" if semester == 1 else f"{year}-11-01 12:00:00")

def get_semester_end(year, semester):
    """
    Returns the end of a SALT observing semester (the start of the next one).

    Args:
        year (int): The calendar year.
        semester (int): The semester number (1 or 2).

    Returns:
        Time: End of the semester (12:00:00 UTC).
    """
    _check_semester(semester)
    return Time(f"{year}-11-01 12:00:00" if semester == 1 else f"{year+1}-05-01 12:00:00")

def get_semester_nights(year, semester, observer=None):
    """
    Generates a sequence of observing nights for an entire semester.

    A "night" is defined as the period between evening astronomical 
    twilight (-18° altitude) and morning astronomical twilight. Twilight
    times are found by linear interpolation of the Sun's altitude on an 
    hourly grid, so they are accurate to about a minute.

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
    num_days = round((end_time - start_time).to(u.day).value)
    
    # Hourly grid; the semester starts at noon so the first crossing is an evening.
    grid_times = start_time + np.arange(num_days * 24 + 1) * u.hour
    sun_coords = get_sun(grid_times)
    sun_alts = sun_coords.transform_to(
        AltAz(obstime=grid_times, location=observer.location)).alt.deg

    twilight = -18.0
    below = sun_alts < twilight
    evening_idx = np.where(~below[:-1] & below[1:])[0]
    morning_idx = np.where(below[:-1] & ~below[1:])[0]

    def _crossing(idx):
        v1, v2 = sun_alts[idx], sun_alts[idx + 1]
        frac = (twilight - v1) / (v2 - v1)
        return grid_times[idx] + frac * (grid_times[idx + 1] - grid_times[idx])

    evenings = _crossing(evening_idx)
    mornings = _crossing(morning_idx)

    nights = []
    for i, eve in zip(range(len(evening_idx)), evenings):
        # Each evening pairs with the first morning crossing after it.
        j = np.searchsorted(morning_idx, evening_idx[i], side="right")
        if j >= len(morning_idx) or eve >= end_time:
            continue
        nights.append((eve, mornings[j]))
    return nights
