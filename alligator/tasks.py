import json
import uuid

from .constants import WAITING, SUCCESS, FAILED, RETRYING, CANCELED
from .utils import determine_module, determine_name, import_attr


class Task(object):
    def __init__(
        self, task_id=None, retries=0, async=True, on_start=None,
        on_success=None, on_error=None, depends_on=None
    ):
        """
        A base class for managing the execution & serialization of tasks.

        Ex::

            from alligator import Task

            # Create the task itself.
            task = Task()
            # ...or...
            task = Task(task_id='my-unique-id', retries=4, async=False)

            # Hook up what will be called when the task comes off the queue.
            task.to_call(email_followers, emails=user.followers.emails())

        :param task_id: (Optional) A unique identifier for the task. Defaults
            to ``None`` (create an ``uuid4``).
        :type task_id: string

        :param retries: (Optional) The number of times to retry a task if it
            fails (throws an exception). Defaults to ``0`` (no retries).
        :type retries: integer

        :param async: (Optional) If the task should be run asynchronously or
            not. Defaults to ``True``.
        :type async: bool

        :param on_start: (Optional) A hook function to run when the task is
            first pulled off the queue. Defaults to ``None``.
        :type on_start: function

        :param on_success: (Optional) A hook function to run when the task
            completes successfully. Defaults to ``None``.
        :type on_success: function

        :param on_error: (Optional) A hook function to run when the task is
            fails. If a non-zero number of retries are provided, this will fire
            **each time** the task fails. Defaults to ``None``.
        :type on_error: function

        :param depends_on: (Optional) A list of task_ids that must be complete
            before this task will fire. Defaults to ``None``.
        :type depends_on: list
        """
        self.task_id = task_id
        self.retries = int(retries)
        self.async = async
        self.status = WAITING
        self.on_start = on_start
        self.on_success = on_success
        self.on_error = on_error
        self.depends_on = depends_on

        self.func = None
        self.func_args = []
        self.func_kwargs = {}

        if self.task_id is None:
            self.task_id = str(uuid.uuid4())

    def to_call(self, func, *args, **kwargs):
        """
        Sets the function & its arguments to be called when the task is
        processed.

        Ex::

            task.to_call(my_function, 1, 'c', another=True)

        :param func: The callable with business logic to execute
        :type func: callable

        :param args: Positional arguments to pass to the callable task
        :type args: list

        :param kwargs: Keyword arguments to pass to the callable task
        :type kwargs: dict
        """
        self.func = func
        self.func_args = args
        self.func_kwargs = kwargs

    def to_waiting(self):
        """
        Sets the task's status as "waiting".

        Useful for the ``on_start/on_success/on_failed`` hook methods for
        figuring out what the status of the task is.
        """
        self.status = WAITING

    def to_success(self):
        """
        Sets the task's status as "success".

        Useful for the ``on_start/on_success/on_failed`` hook methods for
        figuring out what the status of the task is.
        """
        self.status = SUCCESS

    def to_failed(self):
        """
        Sets the task's status as "failed".

        Useful for the ``on_start/on_success/on_failed`` hook methods for
        figuring out what the status of the task is.
        """
        self.status = FAILED

    def to_canceled(self):
        """
        Sets the task's status as "canceled".

        Useful for the ``on_start/on_success/on_failed`` hook methods for
        figuring out what the status of the task is.
        """
        self.status = CANCELED

    def to_retrying(self):
        """
        Sets the task's status as "retrying".

        Useful for the ``on_start/on_success/on_failed`` hook methods for
        figuring out what the status of the task is.
        """
        self.status = RETRYING

    def serialize(self):
        """
        Serializes the ``Task`` data for storing in the queue.

        All data must be JSON-serializable in order to be stored properly.

        :returns: A JSON strong of the task data.
        """
        data = {
            'task_id': self.task_id,
            'retries': self.retries,
            'async': self.async,
            'module': determine_module(self.func),
            'callable': determine_name(self.func),
            'args': self.func_args,
            'kwargs': self.func_kwargs,
            'options': {},
        }

        if self.on_start:
            data['options']['on_start'] = {
                'module': determine_module(self.on_start),
                'callable': determine_name(self.on_start),
            }

        if self.on_success:
            data['options']['on_success'] = {
                'module': determine_module(self.on_success),
                'callable': determine_name(self.on_success),
            }

        if self.on_error:
            data['options']['on_error'] = {
                'module': determine_module(self.on_error),
                'callable': determine_name(self.on_error),
            }

        return json.dumps(data)

    @classmethod
    def deserialize(cls, data):
        """
        Given some data from the queue, deserializes it into a ``Task``
        instance.

        The data must be similar in format to what comes from
        ``Task.serialize`` (a JSON-serialized dictionary). Required keys are
        ``task_id``, ``retries`` & ``async``.

        :param data: A JSON-serialized string of the task data
        :type data: string

        :returns: A populated task
        :rtype: A ``Task`` instance
        """
        data = json.loads(data)
        options = data.get('options', {})

        task = cls(
            task_id=data['task_id'],
            retries=data['retries'],
            async=data['async']
        )

        func = import_attr(data['module'], data['callable'])
        task.to_call(func, *data.get('args', []), **data.get('kwargs', {}))

        if options.get('on_start'):
            task.on_start = import_attr(
                options['on_start']['module'],
                options['on_start']['callable']
            )

        if options.get('on_success'):
            task.on_success = import_attr(
                options['on_success']['module'],
                options['on_success']['callable']
            )

        if options.get('on_error'):
            task.on_error = import_attr(
                options['on_error']['module'],
                options['on_error']['callable']
            )

        return task

    def run(self):
        """
        Runs the task.

        This fires the ``on_start`` hook function first (if present), passing
        the task itself.

        Then it runs the target function supplied via ``Task.to_call`` with
        its arguments & stores the result.

        If the target function succeeded, the ``on_success`` hook function is
        called, passing both the task & the result to it.

        If the target function failed (threw an exception), the ``on_error``
        hook function is called, passing both the task & the exception to it.
        Then the exception is re-raised.

        Finally, the result is returned.
        """
        if self.on_start:
            self.on_start(self)

        try:
            result = self.func(*self.func_args, **self.func_kwargs)
        except Exception as err:
            self.to_failed()

            if self.on_error:
                self.on_error(self, err)

            raise

        self.to_success()

        if self.on_success:
            self.on_success(self, result)

        return result
