class AlligatorException(Exception):
    pass


class TaskFailed(AlligatorException):
    pass


class UnknownModuleError(AlligatorException):
    pass


class UnknownCallableError(AlligatorException):
    pass
