Detailed User Guide
=================

This guide provides a comprehensive breakdown of every component in the ``saltshaker`` package and how they work together to plan SALT observations.

Core Concepts: The Model
------------------------

At the heart of ``saltshaker`` is the **Tracking Model**. Because SALT's fixed-altitude geometry is complex, the package uses empirical data to provide fast, accurate calculations.

SaltTrackingModel (The Singleton)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``SaltTrackingModel`` class contains the raw mathematical logic for SALT's visibility. It is implemented as a **Singleton**, meaning the large visibility data file is only loaded once per session.

*   **When to use it:** You rarely need to interact with this class directly. The ``SaltObserver`` and planning functions handle it for you.
*   **Key Logic:** It differentiates between **East Tracks** (target rising) and **West Tracks** (target setting).

The Observer: SaltObserver
--------------------------

The ``SaltObserver`` class is your primary entry point for Object-Oriented planning. It extends the standard ``astroplan.Observer`` class.

*   **Initialization:** When you create a ``SaltObserver``, it is automatically configured with SALT's precise latitude, longitude, and elevation.
*   **Integration:** Because it inherits from ``astroplan``, you can use it with any standard ``astroplan`` function (like calculating twilight, airmass, or moon position).

Planning Functions: The Functional API
--------------------------------------

For users who prefer a functional style or are building automated scripts, ``saltshaker`` provides high-level functions that don't require managing an observer object.

Visibility Windows
~~~~~~~~~~~~~~~~~~

*   **Function:** ``get_visibility_windows(target, date)``
*   **Returns:** A list of ``VisibilityWindow`` objects.
*   **What it does:** It tells you exactly when (in UTC) a target will enter and exit SALT's visibility annulus on a specific night. It automatically clips these windows to the 24-hour period starting at noon UTC.

Track Lengths
~~~~~~~~~~~~~

*   **Function:** ``get_track_length(target, time)``
*   **Returns:** An Astropy Quantity (seconds).
*   **What it does:** This is the most critical function for feasibility. It tells you how many seconds of tracking are remaining *at a specific moment*. If this is 0, the target is not currently visible.

Rapid Screening
~~~~~~~~~~~~~~~

*   **Function:** ``is_target_observable(target)``
*   **Returns:** Boolean (True/False).
*   **What it does:** A "quick-look" function. It checks if a target's declination is within SALT's reachable range (-75° to +10°). Use this to filter large catalogs before doing detailed time-consuming calculations.

Scheduling: astroplan Constraints
---------------------------------

``saltshaker`` provides two custom constraints that plug directly into the ``astroplan`` scheduling system.

SaltTrackLengthConstraint
~~~~~~~~~~~~~~~~~~~~~~~~~

*   **Purpose:** Ensures your exposure won't be "cut off" by the tracker limit.
*   **Example:** If you set ``min_track_length=1200*u.second``, ``astroplan`` will only mark a time as "observable" if the telescope can track the target for at least 20 continuous minutes from that start time.

SaltMoonConstraint
~~~~~~~~~~~~~~~~~~

*   **Purpose:** Enforces lunar phase requirements.
*   **Unique Logic:** This constraint is satisfied if the Moon's illumination is below your limit **OR** if the Moon is currently below the horizon. This is more accurate for SALT proposals than a simple illumination check.

Semester Management
-------------------

SALT's operations are divided into two semesters. These utilities help with long-term project planning.

*   **``get_semester_start`` / ``get_semester_end``**: Returns the exact ``Time`` objects for the start and end of a given SALT semester.
*   **``get_semester_nights``**: A powerful generator that returns a list of every single night in a semester. Each night is provided as a tuple of ``(evening_astronomical_twilight, morning_astronomical_twilight)``.
