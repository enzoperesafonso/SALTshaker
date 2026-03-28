The Theory of SALT Visibility
=============================

The Southern African Large Telescope (SALT) is a highly unusual 10-meter class optical telescope. Unlike most traditional telescopes, which can point anywhere in the sky (Altitude-Azimuth or Equatorial mounts), SALT has a **fixed-altitude design**.

The Fixed-Altitude Constraint
-----------------------------

SALT is permanently tilted at an angle of **37 degrees** from the zenith (an altitude of 53 degrees). The entire massive telescope structure only rotates horizontally on its azimuth track. 

Because of this, SALT cannot "nod" up and down. To observe an object, SALT must rotate its azimuth to wait for the object to naturally drift through its 12-degree-wide "visibility annulus" (a ring in the sky defined by its 37-degree tilt) as the Earth rotates.

The Tracker
-----------

Once a target enters the annulus, the primary mirror remains stationary. Instead, a complex payload at the top of the telescope, called the **tracker**, physically moves across the focal plane to follow the star. 

Because the focal plane is curved and the tracker has a limited physical range of motion, a target can only be tracked for a limited amount of time. This is called the **Track Length**.

Track Length Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~

The track length depends entirely on the target's **declination** and its current **hour angle** (how far it is from the meridian):

1. **Maximum Track Time:** Depending on the declination, the maximum possible track length ranges from about 45 minutes to over 2 hours.
2. **Declination Limits:** SALT can only observe targets with declinations roughly between **-75° and +10°**.

East, West, and the Zenith Hole
-------------------------------

When tracking a target, one of three scenarios will happen depending on its declination:

1. **Two Tracks (East and West):** The target rises, enters the annulus on the East, and SALT tracks it. Eventually, the target gets *too high* in the sky (it enters the "zenith hole" where SALT cannot point). Tracking stops. Later, as the target sets, it drops back down into the annulus on the West, allowing a second observation window.
2. **One Continuous Track (Grazing):** The target has a declination that causes it to just graze the top edge of the annulus. It never enters the zenith hole, allowing one very long, continuous track.
3. **No Tracks:** The target's declination is too far North or too far South. It never enters the annulus.

This is why `saltshaker` calculations explicitly look for and differentiate between **East Tracks** and **West Tracks**.

Calculating Visibility
----------------------

Because the geometry is complex, calculating analytical track lengths is computationally expensive. `saltshaker` solves this by using the ``SaltTrackingModel``, which loads pre-computed empirical tracking data and performs fast linear interpolation to determine exactly when tracks begin and end, and exactly how many seconds of tracking are available at any given second.
