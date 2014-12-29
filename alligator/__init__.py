from .constants import WAITING, SUCCESS, FAILED, ALL
from .gator import Gator
from .tasks import Task
from .workers import Worker

__author__ = 'Daniel Lindsley'
__version__ = (0, 1, 0, 'dev')
__license__ = 'BSD'


def version():
    short = '.'.join([str(bit) for bit in __version__[:3]])
    return '-'.join([short] + [str(bit) for bit in __version__[3:]])
