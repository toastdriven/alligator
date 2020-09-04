from .constants import WAITING, SUCCESS, FAILED, ALL
from .gator import Gator
from .tasks import Task
from .workers import Worker

__author__ = "Daniel Lindsley"
__version__ = (1, 0, 0, "alpha", 2)
__license__ = "BSD"


def version():
    """
    Returns a human-readable version string.

    For official releases, it will follow a semver style (e.g. ``1.2.7``).
    For dev versions, it will have the semver style first, followed by
    hyphenated qualifiers (e.g. ``1.2.7-dev``).

    Returns a string.
    """
    short = ".".join([str(bit) for bit in __version__[:3]])
    return "-".join([short] + [str(bit) for bit in __version__[3:]])
