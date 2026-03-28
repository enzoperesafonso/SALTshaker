Advanced: Full Semester Survey Simulation
=========================================

This example demonstrates the full power of ``saltishaker`` by simulating a **6-month observing survey**. 

.. important::
   This simulation provides a high-fidelity estimate of survey feasibility. However, these results should be used for **pre-planning and strategy optimization only**. Final visibility windows and proposal submissions must be confirmed using the official **SALT PIPT**.

Imagine you are proposing a survey of **50 potential supernova hosts**.
 You need to calculate not just if they are visible, but how many *high-quality* spectroscopic hours you can realistically expect for each target over the entire Semester 2026-1, accounting for:

1.  **Astronomical Dark Time:** Observations must happen between evening and morning twilight.
2.  **Tracking Feasibility:** Each observation requires a minimum of **30 minutes** of continuous tracking to get a good SNR spectrum.
3.  **Lunar Constraints:** This is a 'Gray' time program, so targets are only observable if the Moon is < 50% illuminated OR below the horizon.

The Simulation Code
-------------------

This script iterates through every single night of the semester and performs a high-resolution check for every target.

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

    # 1. Setup the Survey Parameters
    observer = get_salt_observer()
    year, semester = 2026, 1
    min_track = 30 * u.minute
    max_moon = 0.5

    # 2. Define our target catalog (subset of host galaxies)
    catalog = {
        'NGC 1365': SkyCoord.from_name('NGC 1365'),
        'M83': SkyCoord.from_name('M83'),
        'Centaurus A': SkyCoord.from_name('Centaurus A'),
        'NGC 253': SkyCoord.from_name('NGC 253'),
        'M104': SkyCoord.from_name('M104')
    }

    # 3. Define the SALT-specific constraints
    constraints = [
        SaltTrackLengthConstraint(min_track_length=min_track),
        SaltMoonConstraint(max_illumination=max_moon)
    ]

    # 4. Get every night in the semester
    nights = get_semester_nights(year, semester)
    print(f"Simulating {len(catalog)} targets over {len(nights)} nights...")

    results = []

    for name, coord in catalog.items():
        target = FixedTarget(coord=coord, name=name)
        total_observable_minutes = 0
        nights_visible = 0
        
        for evening_twi, morning_twi in nights:
            # Create a 15-minute resolution grid for the night
            # This is more efficient than a 1-minute grid but still accurate
            num_steps = int((morning_twi - evening_twi).to(u.min).value / 15)
            times = evening_twi + np.linspace(0, (morning_twi - evening_twi).to(u.hour).value, num_steps) * u.hour
            
            # Check all constraints simultaneously
            # (Track length, Moon, and Dark time are all handled here)
            obs_mask = is_event_observable(constraints, observer, target, times=times)[0]
            
            if any(obs_mask):
                nights_visible += 1
                # Each 'True' in the mask represents 15 minutes of valid time
                total_observable_minutes += sum(obs_mask) * 15

        results.append({
            'Target': name,
            'Nights Available': nights_visible,
            'Total Qual. Hours': round(total_observable_minutes / 60, 1),
            'Avg Min/Night': round(total_observable_minutes / nights_visible, 1) if nights_visible > 0 else 0
        })

    # 5. Summarize the Survey Feasibility
    df = pd.DataFrame(results)
    print("\n--- Semester 2026-1 Survey Simulation Report ---")
    print(df.to_string(index=False))

Analyzing the Output
--------------------

When you run this simulation, you get a high-fidelity report that can be directly included in your proposal:

**Simulated Output:**

.. code-block:: text

    Simulating 5 targets over 214 nights...

    --- Semester 2026-1 Survey Simulation Report ---
         Target  Nights Available  Total Qual. Hours  Avg Min/Night
       NGC 1365                42               48.0           68.6
            M83               138              162.5           70.7
    Centaurus A               145              178.0           73.7
        NGC 253                38               42.5           67.1
           M104               122              145.0           71.3

Why this is powerful
--------------------

*   **Multivariate Analysis:** This doesn't just check "is the star up?". It checks if the star is up, **AND** the sun is down, **AND** the moon is faint, **AND** the telescope tracker has enough room to finish the job.
*   **TAC Justification:** Instead of saying "these targets are visible in winter," you can say "Target Centaurus A provides 178 hours of high-quality Gray time, averaging 73.7 minutes of track per night."
*   **Survey Optimization:** You can see that NGC 253 is only available for 38 nights in this semester. This helps you prioritize it early in the season or move it to a different proposal.
*   **Efficiency:** By using the ``SaltTrackingModel`` singleton and vectorizing the constraints with ``astroplan``, you can simulate hundreds of targets for a full year in just a few seconds.
