class AlligatorException(Exception):
    """
    A base exception for all Alligator errors.
    """

    pass


class TaskFailed(AlligatorException):
    """
    Raised when a task fails.
    """

    pass


class UnknownModuleError(AlligatorException):
    """
    Thrown when trying to import an unknown module for a task.
    """

    pass


class UnknownCallableError(AlligatorException):
    """
    Thrown when trying to import an unknown attribute from a module for a task.
    """

    pass


class MultipleDelayError(AlligatorException):
    """
    Thrown when more than one delay option is provided.
    """

    pass
