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

Checking Current Track Length
-----------------------------

Check how many seconds of tracking are remaining for a target at a specific moment.

.. code-block:: python

    from saltshaker import get_track_length
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    import astropy.units as u

    target = SkyCoord.from_name("Sirius")
    check_time = Time("2026-01-15 20:00:00")

    rem = get_track_length(target, check_time)
    print(f"Remaining track length: {rem}")
    print(f"In minutes: {rem.to(u.min):.2f}")

Working with Semesters
----------------------

Retrieve official SALT semester dates and iterate through nights.

.. code-block:: python

    from saltshaker import get_semester_start, get_semester_end, get_semester_nights

    year, semester = 2026, 1

    start = get_semester_start(year, semester)
    end = get_semester_end(year, semester)
    print(f"Semester {year}-{semester} runs from {start.iso} to {end.iso}")

    # Get the first 5 nights of the semester
    nights = get_semester_nights(year, semester)
    for evening, morning in nights[:5]:
        print(f"Night: {evening.iso} to {morning.iso}")

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
    print(f"Current track length: {length}")
