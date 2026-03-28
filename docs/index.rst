saltishaker: Observation Planning for SALT
==========================================

.. image:: _static/salt_shaker_logo.png
   :align: center
   :width: 400px
   :alt: SALTishaker Logo

.. image:: https://img.shields.io/badge/python-3.12+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.12+

.. image:: https://img.shields.io/badge/astropy-powered-orange.svg
   :target: https://www.astropy.org/
   :alt: Powered by Astropy

Welcome to the documentation for **saltishaker**, a specialized Python package for planning astronomical observations with the Southern African Large Telescope (SALT).

Because SALT operates with a unique fixed-altitude design (permanently pointing 37 degrees from the zenith), planning observations requires calculating complex visibility tracks based on Earth's rotation and a physical payload tracker. ``saltishaker`` handles these calculations for you, seamlessly integrating with the broader ``astroplan`` ecosystem.

What can saltishaker do?
------------------------

* **Visibility Windows:** Calculate exactly when (UTC) a specific star or galaxy will drift into SALT's field of view.
* **Track Lengths:** Determine how long SALT can track a target before it hits the edge of its operational limits.
* **Astroplan Integration:** Use SALT's unique tracking and lunar constraints alongside standard airmass and altitude constraints in ``astroplan``.
* **Semester Planning:** Automatically map out visibility statistics over the entire 6-month SALT observing semesters.

Getting Started
---------------

If you are new to SALT, we highly recommend reading the :doc:`Theory of SALT Visibility <theory>` to understand how the telescope moves and tracks targets.

Then, head over to the :doc:`Installation <installation>` and :doc:`Getting Started <getting_started>` guides!

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   theory
   user_guide
   getting_started

.. toctree::
   :maxdepth: 2
   :caption: Examples

   basic_examples
   examples
   advanced_example

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
