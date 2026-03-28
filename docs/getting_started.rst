Getting Started
===============

Installation
------------

You can install ``saltshaker`` via pip (once published) or by cloning the repository:

.. code-block:: bash

    git clone https://github.com/enzo-peres-afonso/saltishaker.git
    cd saltishaker
    poetry install

Basic Concepts
--------------

SALT is a fixed-altitude telescope. This means:

* **Fixed Elevation:** It always points at 37 degrees altitude.
* **Azimuth Rotation:** It can rotate 360 degrees to find targets.
* **Tracking:** It uses a tracker at the focal plane to follow objects as they move across its field of view.

Visibility Annulus
------------------

Because of this design, a target is only visible when its position on the sky intersects SALT's "annulus" (a ring-shaped zone). 

1. **East Track:** The target enters the ring while rising.
2. **Zenith Hole:** The target passes inside the ring (too high for SALT to see).
3. **West Track:** The target re-enters the ring while setting.

Two Ways to Use saltishaker
---------------------------

``saltishaker`` provides both an **Object-Oriented** API (using a ``SaltObserver`` object) and a **Functional** API (using standalone functions). Both are equally valid and return the same results.

Using the SaltObserver (Object-Oriented)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``SaltObserver`` class extends ``astroplan.Observer`` and provides convenient methods:

.. code-block:: python

    from saltshaker import get_salt_observer
    from astropy.coordinates import SkyCoord
    from astropy.time import Time

    # Initialize the observer
    observer = get_salt_observer()

    # Define a target and time
    target = SkyCoord.from_name("Sirius")
    time = Time("2026-01-15 12:00:00")

    # Get visibility windows
    windows = observer.get_tracks(target, time)

    for w in windows:
        print(f"Visible from {w.start_time_utc} to {w.end_time_utc}")

Using Planning Functions (Functional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you prefer not to manage an observer object, you can use standalone functions directly:

.. code-block:: python

    from saltshaker import get_visibility_windows, get_track_length
    from astropy.coordinates import SkyCoord
    from astropy.time import Time

    target = SkyCoord.from_name("Sirius")
    time = Time("2026-01-15 12:00:00")

    # Get windows directly
    windows = get_visibility_windows(target, time)

    # Check track length at a specific moment
    length = get_track_length(target, time + 6*u.hour)
    print(f"Available tracking: {length.to('min'):.1f} minutes")
