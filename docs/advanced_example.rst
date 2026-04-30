Advanced Example: Semester-level Planning
=======================================

This example demonstrates how ``saltshaker`` can be used to help plan and prioritize observations across an entire **6-month observing semester**. 

.. important::
   This example is provided for **pre-planning and strategy optimization only**. While it uses high-fidelity models, all visibility windows, track lengths, and final proposal details **must** be confirmed using the official **SALT Phase I Proposal Tool (PIPT)**. These results should be used as a guide to help you select and prioritize targets before performing final validation in the PIPT.

Target Prioritization and Feasibility
-------------------------------------

When preparing a proposal for a multi-target project (such as a survey of transient hosts), it is helpful to understand the relative availability of your targets. This allows you to prioritize which objects to include in your final PIPT submission.

In this example, we evaluate a list of targets against several constraints:

1.  **Astronomical Dark Time:** Preliminary check between evening and morning twilight.
2.  **Tracking Requirements:** Requiring a minimum of **30 minutes** of continuous tracking for each observation window.
3.  **Lunar Constraints:** Filtering for 'Gray' time requirements (Moon < 50% illuminated OR below the horizon).

Example Planning Script
-----------------------

This script iterates through the nights of a semester to provide a rough estimate of the total available observing time for each target.

.. code-block:: python

    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    from astroplan import FixedTarget, is_event_observable
    import numpy as np
    import pandas as pd
    from saltshaker import (
        get_salt_observer, 
        get_semester_nights, 
        SaltTrackLengthConstraint, 
        SaltMoonConstraint
    )

    # 1. Setup the Planning Parameters
    observer = get_salt_observer()
    year, semester = 2026, 1
    min_track = 30 * u.minute
    max_moon = 0.5

    # 2. Define a preliminary target list
    catalog = {
        'NGC 1365': SkyCoord.from_name('NGC 1365'),
        'M83': SkyCoord.from_name('M83'),
        'Centaurus A': SkyCoord.from_name('Centaurus A'),
        'NGC 253': SkyCoord.from_name('NGC 253'),
        'M104': SkyCoord.from_name('M104')
    }

    # 3. Define SALT-specific constraints for pre-planning
    constraints = [
        SaltTrackLengthConstraint(min_track_length=min_track),
        SaltMoonConstraint(max_illumination=max_moon)
    ]

    # 4. Iterate through the semester
    nights = get_semester_nights(year, semester)
    print(f"Evaluating {len(catalog)} targets over {len(nights)} nights...")

    results = []

    for name, coord in catalog.items():
        target = FixedTarget(coord=coord, name=name)
        total_observable_minutes = 0
        nights_visible = 0
        
        for evening_twi, morning_twi in nights:
            # Use a 15-minute resolution for preliminary estimates
            num_steps = int((morning_twi - evening_twi).to(u.min).value / 15)
            times = evening_twi + np.linspace(0, (morning_twi - evening_twi).to(u.hour).value, num_steps) * u.hour
            
            # Check constraints
            obs_mask = is_event_observable(constraints, observer, target, times=times)[0]
            
            if any(obs_mask):
                nights_visible += 1
                total_observable_minutes += sum(obs_mask) * 15

        results.append({
            'Target': name,
            'Nights Available': nights_visible,
            'Est. Total Hours': round(total_observable_minutes / 60, 1),
            'Est. Avg Min/Night': round(total_observable_minutes / nights_visible, 1) if nights_visible > 0 else 0
        })

    # 5. Review the results
    df = pd.DataFrame(results)
    print("\n--- Preliminary Semester 2026-1 Planning Report ---")
    print(df.to_string(index=False))

Understanding the Report
------------------------

The output of this script provides a baseline to help guide your observing strategy:

**Example Output:**

.. code-block:: text

    Evaluating 5 targets over 214 nights...

    --- Preliminary Semester 2026-1 Planning Report ---
         Target  Nights Available  Est. Total Hours  Est. Avg Min/Night
       NGC 1365                48              26.5                33.1
            M83               103              72.2                42.1
    Centaurus A               106              89.5                50.7
        NGC 253                79              44.0                33.4
           M104                89              82.2                55.4

Strategic Benefits
------------------

*   **Multivariate Preliminary Check:** This approach accounts for the interaction between dark time, lunar phase, and SALT's physical tracking annulus simultaneously.
*   **Strategy Guidance:** The report helps identify which targets have limited availability (e.g., NGC 253 in this example), allowing you to focus on them when they are best placed.
*   **Time Request Justification:** These estimates provide a quantitative basis for the time requests you will ultimately define and validate in the official SALT PIPT.
*   **Comprehensive Screening:** This example allows you to screen multiple targets across a broad timeframe, identifying the most promising candidates for your project before performing the mandatory final checks in the official tools.
