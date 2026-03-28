Proposer's Cookbook: Planning for SALT
========================================

This page provides detailed recipes for using ``saltshaker`` to prepare observing proposals for the Southern African Large Telescope (SALT). 

When writing a proposal, you must demonstrate that your targets are observable within the requested semester, that you have sufficient track length for your exposures, and that you have accounted for constraints like Moon brightness.

.. contents:: Table of Contents
   :local:
   :depth: 2

Feasibility: Determining Track Lengths
--------------------------------------

The most fundamental constraint at SALT is the tracker's physical range. For any exposure, you must ensure the telescope can follow the target for the required duration. 

The following plot is useful for your Technical Justification to show the available "window of opportunity" for your longest exposures.

.. plot::

    import numpy as np
    import matplotlib.pyplot as plt
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    import astropy.units as u
    from saltshaker import get_track_length

    # Define your target and the night of interest
    target = SkyCoord.from_name('Sirius')
    obs_date = '2026-01-15'
    start_time = Time(f"{obs_date} 12:00:00")

    # Sample the tracking zone over 24 hours
    times = start_time + np.linspace(0, 24, 1000) * u.hour
    track_lengths = [get_track_length(target, t).to(u.second).value for t in times]

    plt.figure(figsize=(10, 5))
    plt.fill_between(times.plot_date, track_lengths, color='red', alpha=0.1)
    plt.plot(times.plot_date, track_lengths, color='red', lw=2)
    
    # Add a reference line for a typical 30-minute exposure
    plt.axhline(1800, color='black', linestyle='--', label='30 min Exposure')

    plt.title(f"Available Tracking Time for {target.name}")
    plt.ylabel("Available Track Length (seconds)")
    plt.xlabel("Time (UTC)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

Nightly Planning: Visualizing Tracks
------------------------------------

Because SALT is a fixed-altitude telescope, targets pass through the visibility zone twice on many nights (the East and West tracks), separated by a "Zenith Hole." 

Use this plot to visualize when your target is observable relative to **astronomical twilight** (-18°).

.. plot::

    from saltshaker import get_visibility_windows, get_salt_observer
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    import astropy.units as u
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter

    observer = get_salt_observer()
    target = SkyCoord.from_name('Sirius')
    date = '2026-01-15'

    # 1. Calculate the tracks and twilight
    windows = get_visibility_windows(target, date)
    start_time = Time(f"{date} 12:00:00")
    eve_twi = observer.twilight_evening_astronomical(start_time, which='next')
    morn_twi = observer.twilight_morning_astronomical(eve_twi, which='next')

    # 2. Create the visualization
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Shade the dark time
    ax.axvspan(eve_twi.plot_date, morn_twi.plot_date, color='black', alpha=0.15, label='Astronomical Dark')

    # Shade the visibility windows
    for i, w in enumerate(windows):
        ax.axvspan(w.start_time.plot_date, w.end_time.plot_date, color='green', alpha=0.6, 
                   label='SALT Visibility' if i==0 else "")
        # Label the tracks
        mid_time = w.start_time.plot_date + (w.end_time.plot_date - w.start_time.plot_date)/2
        ax.text(mid_time, 0.5, f"Track {i+1}", ha='center', va='center', fontweight='bold')

    plt.title(f"Nightly Observation Windows: {target.name} on {date}")
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.set_yticks([])
    plt.xlabel("Time (UTC)")
    plt.legend(loc='upper right')
    plt.grid(True, axis='x', alpha=0.3)
    plt.show()

Scheduling: Moon and Track Length Constraints
---------------------------------------------

Proposals often require specific "Lunar Class" (Dark, Gray, or Bright). Using ``saltishaker`` with ``astroplan`` allows you to precisely calculate when your target meets both SALT's tracking requirements and your project's lunar constraints.

.. plot::

    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    from astroplan import FixedTarget, is_event_observable
    from saltshaker import (
        get_salt_observer, 
        SaltTrackLengthConstraint, 
        SaltMoonConstraint
    )
    import numpy as np
    import matplotlib.pyplot as plt

    observer = get_salt_observer()
    target = FixedTarget(coord=SkyCoord.from_name('Sirius'), name='Sirius')
    
    # Define constraints for a 'Gray' time proposal:
    # 1. Must have at least 20 minutes of track length
    # 2. Moon must be less than 50% illuminated (or below the horizon)
    constraints = [
        SaltTrackLengthConstraint(min_track_length=20 * u.minute),
        SaltMoonConstraint(max_illumination=0.5)
    ]

    # Evaluate over a 48-hour period
    times = Time('2026-01-15 12:00:00') + np.linspace(0, 48, 200) * u.hour
    observable = is_event_observable(constraints, observer, target, times=times)[0]

    plt.figure(figsize=(10, 2))
    plt.fill_between(times.plot_date, 0, 1, where=observable, color='blue', alpha=0.3)
    plt.title(f"Observability with Gray Moon & >20m Track: {target.name}")
    plt.xlabel("Time (UTC)")
    plt.yticks([])
    plt.show()

Long-term Planning: Annual Visibility
-------------------------------------

For any multi-month proposal, you need to show when your target is best placed during the semester. The "Annual Plot" shows how the visibility windows drift across the night as the year progresses.

.. plot::

    import numpy as np
    import matplotlib.pyplot as plt
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    import astropy.units as u
    from saltshaker import get_salt_observer, get_visibility_windows
    from matplotlib.lines import Line2D

    observer = get_salt_observer()
    target = SkyCoord.from_name('Sirius')
    year = 2026
    
    # Sample every 10 days
    dates = Time(f"{year}-01-01") + np.arange(0, 365, 10) * u.day
    
    plt.figure(figsize=(10, 8))
    for date in dates:
        windows = get_visibility_windows(target, date)
        try:
            eve = observer.twilight_evening_astronomical(date, which='next')
            morn = observer.twilight_morning_astronomical(eve, which='next')
            base = Time(f"{date.iso.split()[0]} 12:00:00")
            to_h = lambda t: (t - base).to(u.hour).value
            
            # Plot Dark Time
            plt.plot([to_h(eve), to_h(morn)], [date.datetime, date.datetime], color='gray', alpha=0.2, lw=4)
            # Plot SALT Tracks
            for w in windows:
                plt.plot([to_h(w.start_time), to_h(w.end_time)], [date.datetime, date.datetime], color='green', lw=4)
        except: continue

    plt.gca().invert_yaxis()
    plt.title(f"Annual Visibility Cycle: {target.name}")
    plt.xlabel("Hours from Noon UTC")
    plt.grid(True, alpha=0.2)
    plt.show()

Semester Statistics: Justifying Time Requests
---------------------------------------------

A thorough proposal includes statistics on the total number of observable hours in a semester. This helps the TAC (Time Allocation Committee) understand if your project is realistic.

.. code-block:: python

    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from saltshaker import get_visibility_windows, get_semester_nights

    target = SkyCoord.from_name('NGC 300')
    year, semester = 2026, 1
    nights = get_semester_nights(year, semester)
    
    total_sec = 0
    observable_nights = 0

    for eve, morn in nights:
        windows = get_visibility_windows(target, eve)
        night_sec = 0
        for w in windows:
            # Calculate overlap of the SALT track with dark time
            start = max(w.start_time, eve)
            end = min(w.end_time, morn)
            if start < end:
                night_sec += (end - start).to(u.second).value
        
        if night_sec > 0:
            total_sec += night_sec
            observable_nights += 1

    print(f"Proposal Statistics for {target.name} (Semester {year}-{semester}):")
    print(f"  - Total Observable Hours: {total_sec / 3600:.1f} hours")
    print(f"  - Number of Observable Nights: {observable_nights}")
    print(f"  - Average Track per Night: {(total_sec/observable_nights)/60:.1f} minutes")

Batch Screening: Catalog Feasibility
------------------------------------

If your proposal involves a large catalog of targets, you can quickly screen them to find which are best suited for SALT.

.. code-block:: python

    import pandas as pd
    from astropy.coordinates import SkyCoord
    from saltshaker import is_target_observable

    # Load your target catalog
    catalog = [
        ('M31', '00h42m44s', '+41d16m09s'),
        ('M42', '05h35m17s', '-05d23m28s'),
        ('Omega Cen', '13h26m47s', '-47d28m46s'),
        ('Centaurus A', '13h25m27s', '-43d01m08s'),
    ]

    results = []
    for name, ra, dec in catalog:
        coord = SkyCoord(ra, dec, frame='icrs')
        # is_target_observable checks if it EVER enters the SALT annulus
        observable = is_target_observable(coord)
        results.append({'Target': name, 'Dec': dec, 'SALT Observable': observable})

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
