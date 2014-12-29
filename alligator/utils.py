import importlib

from .exceptions import UnknownModuleError, UnknownCallableError


def determine_module(func):
    return func.__module__


def determine_name(func):
    if hasattr(func, '__name__'):
        return func.__name__
    elif hasattr(func, '__class__'):
        return func.__class__.__name__

    # This shouldn't be possible, but blow up if so.
    raise AttributeError("Provided callable '{}' has no name.".format(
        func
    ))


def import_module(module_name):
    try:
        return importlib.import_module(module_name)
    except ImportError as err:
        raise UnknownModuleError(str(err))


def import_attr(module_name, attr_name):
    module = import_module(module_name)

    try:
        return getattr(module, attr_name)
    except AttributeError as err:
        raise UnknownCallableError(str(err))
