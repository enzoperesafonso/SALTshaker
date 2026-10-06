from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from saltshaker.constraints import SaltMoonConstraint, SaltTrackLengthConstraint
from saltshaker.model import SaltTrackingModel, get_model
from saltshaker.observer import SaltObserver, get_salt_observer
from saltshaker.planning import (
    VisibilityWindow,
    get_semester_end,
    get_semester_nights,
    get_semester_start,
    get_track_length,
    get_tracks,
    get_visibility_windows,
    is_target_observable,
    visibility_table,
)

try:
    # The PyPI distribution is named "saltishaker"; the import name is "saltshaker".
    __version__ = _version("saltishaker")
except PackageNotFoundError:  # running from a source checkout without installing
    __version__ = "unknown"

__all__ = [
    "SaltMoonConstraint",
    "SaltObserver",
    "SaltTrackLengthConstraint",
    "SaltTrackingModel",
    "VisibilityWindow",
    "__version__",
    "get_model",
    "get_salt_observer",
    "get_semester_end",
    "get_semester_nights",
    "get_semester_start",
    "get_track_length",
    "get_tracks",
    "get_visibility_windows",
    "is_target_observable",
    "visibility_table",
]
