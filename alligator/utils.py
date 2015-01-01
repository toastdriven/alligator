import importlib

from .exceptions import UnknownModuleError, UnknownCallableError


def determine_module(func):
    """
    Given a function, returns the Python dotted path of the module it comes
    from.

    Ex::

        from random import choice
        determine_module(choice) # Returns 'random'

    :param func: The callable
    :type func: function

    :returns: Dotted path string
    """
    return func.__module__


def determine_name(func):
    """
    Given a function, returns the name of the function.

    Ex::

        from random import choice
        determine_name(choice) # Returns 'choice'

    :param func: The callable
    :type func: function

    :returns: Name string
    """
    if hasattr(func, '__name__'):
        return func.__name__
    elif hasattr(func, '__class__'):
        return func.__class__.__name__

    # This shouldn't be possible, but blow up if so.
    raise AttributeError("Provided callable '{}' has no name.".format(
        func
    ))


def import_module(module_name):
    """
    Given a dotted Python path, imports & returns the module.

    If not found, raises ``UnknownModuleError``.

    Ex::

        mod = import_module('random')

    :param module_name: The dotted Python path
    :type module_name: string

    :returns: module
    """
    try:
        return importlib.import_module(module_name)
    except ImportError as err:
        raise UnknownModuleError(str(err))


def import_attr(module_name, attr_name):
    """
    Given a dotted Python path & an attribute name, imports the module &
    returns the attribute.

    If not found, raises ``UnknownCallableError``.

    Ex::

        choice = import_attr('random', 'choice')

    :param module_name: The dotted Python path
    :type module_name: string

    :param attr_name: The attribute name
    :type attr_name: string

    :returns: attribute
    """
    module = import_module(module_name)

    try:
        return getattr(module, attr_name)
    except AttributeError as err:
        raise UnknownCallableError(str(err))
