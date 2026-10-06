Basic Examples
==============

This page provides simple, direct code snippets for common tasks using ``saltshaker``. These examples focus on the API functionality without complex plotting or scientific justification.

Checking if a Target is Ever Observable
---------------------------------------

Use this to quickly verify if a target's declination is within SALT's reachable range (-76° to +11.25°).

.. code-block:: python

    from saltshaker import is_target_observable
    from astropy.coordinates import SkyCoord

    # Check by name
    target = SkyCoord.from_name("Sirius")
    print(f"Is Sirius observable? {is_target_observable(target)}")

    # Check by raw declination (degrees)
    print(f"Is +45 degrees observable? {is_target_observable(45.0)}")

**Output:**

.. code-block:: text

    Is Sirius observable? True
    Is +45 degrees observable? False

Listing Visibility Windows
--------------------------

Get the exact UTC times when a target enters and exits the SALT visibility annulus.

.. code-block:: python

    from saltshaker import get_visibility_windows
    from astropy.coordinates import SkyCoord

    target = SkyCoord.from_name("Sirius")
    date = "2026-01-15"

    windows = get_visibility_windows(target, date)

    for i, w in enumerate(windows):
        print(f"Track {i+1}: {w.start_time_utc} to {w.end_time_utc} ({w.duration/60:.1f} minutes)")

**Output:**

.. code-block:: text

    Track 1: 2026-01-15 18:40:59 to 2026-01-15 19:44:25 (63.4 minutes)
    Track 2: 2026-01-15 23:37:56 to 2026-01-16 00:42:05 (64.2 minutes)

Checking Current Track Length
-----------------------------

Check how many seconds of tracking are remaining for a target at a specific moment.
Both ``time`` and ``target`` may be arrays, so a whole night can be evaluated in one call.

.. code-block:: python

    from saltshaker import get_track_length
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    import astropy.units as u

    target = SkyCoord.from_name("Sirius")
    check_time = Time("2026-01-15 19:15:00")

    rem = get_track_length(target, check_time)
    print(f"Remaining track length: {rem}")
    print(f"In minutes: {rem.to(u.min):.2f}")

**Output:**

.. code-block:: text

    Remaining track length: 1770.019139696736 s
    In minutes: 29.50 min

Restricting to Astronomical Night
---------------------------------

Visibility windows are purely geometric, so they include daytime. Pass ``night_only=True`` to keep only the parts that fall between evening and morning astronomical twilight (Sun below -18°).

.. code-block:: python

    from saltshaker import get_visibility_windows
    from astropy.coordinates import SkyCoord

    target = SkyCoord.from_name("Sirius")

    windows = get_visibility_windows(target, "2026-01-15", night_only=True)

    for w in windows:
        print(f"{w.start_time_utc[:19]} to {w.end_time_utc[:19]} ({w.duration/60:.1f} minutes)")

**Output:**

.. code-block:: text

    2026-01-15 19:24:04 to 2026-01-15 19:44:25 (20.4 minutes)
    2026-01-15 23:37:56 to 2026-01-16 00:42:05 (64.2 minutes)

Here the first track is shortened because it starts before the end of evening twilight. ``observer.get_tracks(target, date, night_only=True)`` works the same way.

.. note::
    A date-only string such as ``"2026-01-15"`` starts the 24-hour search at 12:00 UTC. A ``Time`` object, or a string that includes a time, is used exactly as the start of the window, and tracks that cross either end of the 24 hours are truncated to it.

Checking Many Times at Once
---------------------------

``get_track_length`` accepts an array of times (and/or an array of targets), so you can evaluate a whole day without a Python loop.

.. code-block:: python

    import numpy as np
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    from saltshaker import get_track_length

    target = SkyCoord.from_name("Sirius")
    times = Time("2026-01-15 12:00:00") + np.arange(0, 24, 4) * u.hour

    print(get_track_length(target, times).to(u.min).round(1))

**Output:**

.. code-block:: text

    [ 0.  0.  0. 42.  0.  0.] min

Screening a Catalog with a Table
--------------------------------

``visibility_table`` returns an ``astropy.table.Table`` with one row per visibility window. Targets that are never observable simply contribute no rows.

.. code-block:: python

    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from saltshaker import visibility_table

    catalog = SkyCoord(
        ra=[101.287, 11.888, 10.685] * u.deg,
        dec=[-16.716, -25.288, 41.269] * u.deg,
    )
    names = ["Sirius", "NGC 253", "M31"]

    table = visibility_table(catalog, "2026-01-15", names=names)
    table.pprint(max_width=-1)

**Output:**

.. code-block:: text

      name     ra     dec        start_utc            end_utc       duration
              deg     deg                                              s    
    ------- ------- ------- ------------------- ------------------- --------
     Sirius 101.287 -16.716 2026-01-15 18:40:59 2026-01-15 19:44:25   3806.4
     Sirius 101.287 -16.716 2026-01-15 23:37:56 2026-01-16 00:42:05   3849.1
    NGC 253  11.888 -25.288 2026-01-15 12:26:26 2026-01-15 13:27:45   3679.1
    NGC 253  11.888 -25.288 2026-01-15 18:01:31 2026-01-15 19:02:49   3678.2

M31 (Dec +41°) has no rows because it is outside SALT's declination range. The table can be saved with ``table.write("windows.csv")`` or converted with ``table.to_pandas()``.

Quick Plot
----------

``plot_visibility`` draws the track length over 24 hours with the visibility windows shaded. It needs matplotlib (``pip install "saltishaker[plot]"``).

.. code-block:: python

    import matplotlib.pyplot as plt
    from saltshaker.plotting import plot_visibility

    ax = plot_visibility("Sirius", "2026-01-15", night_only=True)
    plt.show()

Command Line
------------

The same checks are available from the shell (the ``saltshaker`` command is installed with the package).

.. code-block:: bash

    # Windows for a named target (resolved online), night only
    saltshaker visibility Sirius 2026-01-15 --night-only

    # Or give coordinates in degrees
    saltshaker visibility --ra 101.287 --dec -16.716 2026-01-15

    # Is a declination ever reachable? Only --dec is needed
    saltshaker observable --dec 60

**Output:**

.. code-block:: text

    2026-01-15 19:24:04.612 -> 2026-01-15 19:44:25.779  (20.4 min)
    2026-01-15 23:37:56.714 -> 2026-01-16 00:42:05.788  (64.2 min)

    dec=+60.000 deg: never observable

The exit code is 0 when there is something to report and 1 otherwise, so the commands can be used in shell scripts.

Deprecated: ``get_tracks``
--------------------------

The module-level ``get_tracks(target, date)`` still works but emits a ``DeprecationWarning``. Use ``get_visibility_windows`` instead. (``SaltObserver.get_tracks`` is a supported method and is not deprecated.)

Working with Semesters
----------------------

Retrieve SALT semester dates (semester 1 runs May-October, semester 2 November-April) and iterate through nights.

.. code-block:: python

    from saltshaker import get_semester_start, get_semester_end, get_semester_nights

    year, semester = 2026, 1

    start = get_semester_start(year, semester)
    end = get_semester_end(year, semester)
    print(f"Semester {year}-{semester} runs from {start.iso} to {end.iso}")

    # Get the first 3 nights of the semester
    nights = get_semester_nights(year, semester)
    for evening, morning in nights[:3]:
        print(f"Night: {evening.iso} to {morning.iso}")

**Output:**

.. code-block:: text

    Semester 2026-1 runs from 2026-05-01 12:00:00.000 to 2026-11-01 12:00:00.000
    Night: 2026-05-01 17:21:22.786 to 2026-05-02 03:46:27.794
    Night: 2026-05-02 17:20:33.657 to 2026-05-03 03:47:03.304
    Night: 2026-05-03 17:19:45.749 to 2026-05-04 03:47:38.687

Using the SaltObserver Shortcut
-------------------------------

If you are already using an observer object, you can access these functions as methods.

.. code-block:: python

    from saltshaker import get_salt_observer
    from astropy.coordinates import SkyCoord
    from astropy.time import Time

    observer = get_salt_observer()
    target = SkyCoord.from_name("Sirius")
    time = Time("2026-01-15 19:15:00")

    # Methods match the standalone functions
    windows = observer.get_tracks(target, time)
    length = observer.track_length(target, time)

    print(f"Tracks found: {len(windows)}")
    print(f"Current track length: {length:.1f}")

**Output:**

.. code-block:: text

    Tracks found: 2
    Current track length: 1770.0 s
