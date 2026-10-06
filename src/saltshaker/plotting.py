"""
Quick-look plots for SALT visibility.

Requires ``matplotlib`` (install with ``pip install saltishaker[plot]``).
"""

import astropy.units as u

from saltshaker.planning import _as_skycoord, _resolve_start_time, get_visibility_windows


def plot_visibility(target, obs_date, observer=None, night_only=False, ax=None):
    """
    Plots a target's visibility windows and the track length over 24 hours.

    Args:
        target (SkyCoord | FixedTarget | str): A single target.
        obs_date (str | Time): Start of the 24-hour period (see
            `get_visibility_windows`).
        observer (SaltObserver | None): Observer to use.
        night_only (bool): Clip windows to astronomical night.
        ax (matplotlib.axes.Axes | None): Axes to draw on; created if omitted.

    Returns:
        matplotlib.axes.Axes: The axes containing the plot.
    """
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import numpy as np

    from saltshaker.planning import get_track_length

    target = _as_skycoord(target)
    start = _resolve_start_time(obs_date)
    times = start + np.linspace(0, 24, 24 * 12 + 1) * u.hour
    lengths = get_track_length(target, times, observer=observer).to(u.min).value

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(times.plot_date, lengths, color="k", lw=1)
    for w in get_visibility_windows(target, start, observer=observer, night_only=night_only):
        ax.axvspan(w.start_time.plot_date, w.end_time.plot_date, color="C0", alpha=0.25)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel(f"UTC (from {start.iso[:16]})")
    ax.set_ylabel("Track length [min]")
    ax.set_title("SALT visibility (pre-planning only; validate in PIPT)")
    return ax
