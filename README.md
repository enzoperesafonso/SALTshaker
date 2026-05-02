# saltshaker

<p align="center">
  <img src="salt_shaker_logo.png" width="500" alt="saltshaker Logo">
</p>

<p align="center">
  <a href="https://github.com/enzoperesafonso/saltshaker/actions/workflows/ci.yml">
    <img src="https://github.com/enzoperesafonso/saltshaker/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="https://github.com/enzoperesafonso/saltshaker/releases">
    <img src="https://img.shields.io/github/v/release/enzoperesafonso/saltshaker" alt="Latest Version">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
  </a>
  <a href="https://doi.org/10.5281/zenodo.19878634">
    <img src="https://zenodo.org/badge/1124345702.svg" alt="DOI">
  </a>
</p>

**saltshaker** is a specialized Python package designed for planning and optimizing astronomical observations with the **Southern African Large Telescope (SALT)**.

> [!IMPORTANT]
> **Essential Usage Information:**
> 1. **Independent Tool:** `saltshaker` is a community-developed tool.
> 2. **Pre-Planning Only:** This package is designed for target screening, survey strategy optimization, and preliminary feasibility checks.
> 3. **Mandatory PIPT Validation:** All final visibility windows and observing proposals **must** be validated and submitted using the official SALT Phase I Proposal Tool.

Because SALT operates with a unique fixed-altitude design (pointing permanently at 37 degrees from the zenith), planning observations requires calculating complex visibility tracks based on Earth's rotation and a physical payload tracker. `saltshaker` handles these calculations for you, providing high-performance visibility windows, track lengths, and integration with the broader `astroplan` ecosystem.

## Key Features

*   **Visibility Windows:** Calculate exactly when (UTC) a specific star or galaxy will drift into SALT's field of view.
*   **Track Lengths:** Determine how long SALT can track a target before it hits the edge of its operational limits.
*   **Astroplan Integration:** Use SALT-specific tracking and lunar constraints directly within `astroplan` scheduling.
*   **Semester Planning:** Automatically calculate visibility statistics and nights for entire 6-month SALT observing semesters.
*   **Singleton Tracking Model:** Efficient data loading and high-performance interpolation.

## Installation

To install the package from PyPI:

```bash
pip install saltishaker
```

> [!NOTE]
> Although the package is installed as `saltishaker`, you import it in your code as `saltshaker`.

For development installation:

```bash
git clone https://github.com/enzoperesafonso/saltshaker.git
cd saltshaker
pip install .
```

## Quick Start

```python
from saltshaker import get_salt_observer
from astropy.coordinates import SkyCoord
from astropy.time import Time

# Initialize the observer
observer = get_salt_observer()

# Define a target
target = SkyCoord.from_name("Sirius")
time = Time("2026-01-15 12:00:00")

# Get visibility tracks
tracks = observer.get_tracks(target, time)

for track in tracks:
    print(f"Visible from {track.start_time_utc} to {track.end_time_utc}")
```

## Documentation

Full documentation, including a theoretical background on SALT visibility and a "Proposer's Cookbook" of examples, is available at:

**[https://saltishaker.readthedocs.io/en/latest/](https://saltishaker.readthedocs.io/en/latest/)**

## License

This project is licensed under the MIT License - see the LICENSE file for details.
