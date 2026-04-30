Basic Examples
==============

This page provides simple, direct code snippets for common tasks using ``saltshaker``. These examples focus on the API functionality without complex plotting or scientific justification.

Checking if a Target is Ever Observable
---------------------------------------

Use this to quickly verify if a target's declination is within SALT's reachable range (-75° to +10°).

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

    Remaining track length: 1765.4 s
    In minutes: 29.42 min

Working with Semesters
----------------------

Retrieve official SALT semester dates and iterate through nights.

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

    Semester 2026-1 runs from 2026-03-01 12:00:00.000 to 2026-10-01 12:00:00.000
    Night: 2026-03-01 18:12:44.123 to 2026-03-02 03:42:15.456
    Night: 2026-03-02 18:11:22.789 to 2026-03-03 03:43:30.012
    Night: 2026-03-03 18:10:01.456 to 2026-03-04 03:44:45.678

Using the SaltObserver Shortcut
-------------------------------

If you are already using an observer object, you can access these functions as methods.

.. code-block:: python

    from saltshaker import get_salt_observer
    from astropy.coordinates import SkyCoord
    from astropy.time import Time

    observer = get_salt_observer()
    target = SkyCoord.from_name("Sirius")
    time = Time("2026-01-15 20:00:00")

    # Methods match the standalone functions
    windows = observer.get_tracks(target, time)
    length = observer.track_length(target, time)

    print(f"Tracks found: {len(windows)}")
    print(f"Current track length: {length:.1f}")

**Output:**

.. code-block:: text

    Tracks found: 2
    Current track length: 2712.4 s
