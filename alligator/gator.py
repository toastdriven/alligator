from .constants import ALL
from .tasks import Task
from .utils import import_attr


class Gator(object):
    def __init__(self, conn_string, queue_name=ALL, task_class=Task, backend_class=None):
        """
        A coordination for scheduling & processing tasks.

        Handles creating tasks (with options), using the backend to place tasks
        in the queue & pulling/processing tasks off the queue.

        Ex::

            from alligator import Gator

            def add(a, b):
                return a + b

            gator = Gator('locmem://')

            gator.task(add, 3, 7)

        :param conn_string: A DSN for connecting to the queue. Passed along
            to the backend.
        :type conn_string: string

        :param queue_name: (Optional) The name of the queue the tasks should be
            placed in. Defaults to ``ALL``.
        :type queue_name: string

        :param task_class: (Optional) The class to use for instantiating tasks.
            Defaults to ``Task``.
        :type task_class: class

        :param backend_class: (Optional) The class to use for instantiating
            the backend. Defaults to ``None`` (DSN detection).
        :type backend_class: class
        """
        self.conn_string = conn_string
        self.queue_name = queue_name
        self.task_class = task_class
        self.backend_class = backend_class

        if not backend_class:
            self.backend = self.build_backend(self.conn_string)
        else:
            self.backend = backend_class(self.conn_string)

    def build_backend(self, conn_string):
        """
        Given a DSN, returns an instantiated backend class.

        Ex::

            backend = gator.build_backend('locmem://')
            # ...or...
            backend = gator.build_backend('redis://127.0.0.1:6379/0')

        :param conn_string: A DSN for connecting to the queue. Passed along
            to the backend.
        :type conn_string: string

        :returns: A backend ``Client`` instance
        """
        backend_name, _ = conn_string.split(':', 1)
        backend_path = 'alligator.backends.{}_backend'.format(backend_name)
        client_class = import_attr(backend_path, 'Client')
        return client_class(conn_string)

    def len(self):
        """
        Returns the number of remaining queued tasks.

        :returns: An integer count
        """
        return self.backend.len(self.queue_name)

    def push(self, task, func, *args, **kwargs):
        """
        Pushes a configured task onto the queue.

        Typically, you'll favor using the ``Gator.task`` method or
        ``Gator.options`` context manager for creating a task. Call this
        only if you have specific needs or know what you're doing.

        If the ``Task`` has the ``async = False`` option, the task will be
        run immediately (in-process). This is useful for development and
        in testing.

        Ex::

            task = Task(async=False, retries=3)
            finished = gator.push(task, increment, incr_by=2)

        :param task: A mostly-configured task
        :type task: A ``Task`` instance

        :param func: The callable with business logic to execute
        :type func: callable

        :param args: Positional arguments to pass to the callable task
        :type args: list

        :param kwargs: Keyword arguments to pass to the callable task
        :type kwargs: dict

        :returns: The ``Task`` instance
        """
        task.to_call(func, *args, **kwargs)
        data = task.serialize()

        if task.async:
            task.task_id = self.backend.push(
                self.queue_name,
                task.task_id,
                data
            )
        else:
            self.execute(task)

        return task

    def pop(self):
        """
        Pops a task off the front of the queue & runs it.

        Typically, you'll favor using a ``Worker`` to handle processing the
        queue (to constantly consume). However, if you need to custom-process
        the queue in-order, this method is useful.

        Ex::

            # Tasks were previously added, maybe by a different process or
            # machine...
            finished_topmost_task = gator.pop()

        :returns: The completed ``Task`` instance
        """
        data = self.backend.pop(self.queue_name)

        if data:
            task = self.task_class.deserialize(data)
            return self.execute(task)

    def get(self, task_id):
        """
        Gets a specific task, by ``task_id`` off the queue & runs it.

        Using this is not as performant (because it has to search the queue),
        but can be useful if you need to specifically handle a task *right now*.

        Ex::

            # Tasks were previously added, maybe by a different process or
            # machine...
            finished_task = gator.get('a-specific-uuid-here')

        :param task_id: The identifier of the task to process
        :type task_id: string

        :returns: The completed ``Task`` instance
        """
        data = self.backend.get(self.queue_name, task_id)

        if data:
            task = self.task_class.deserialize(data)
            return self.execute(task)

    def cancel(self, task_id):
        """
        Takes an existing task & cancels it before it is processed.

        Returns the canceled task, as that could be useful in creating a new
        task.

        Ex::

            task = gator.task(add, 18, 9)

            # Whoops, didn't mean to do that.
            gator.cancel(task.task_id)

        :param task_id: The identifier of the task to process
        :type task_id: string

        :returns: The canceled ``Task`` instance
        """
        data = self.backend.get(self.queue_name, task_id)

        if data:
            task = self.task_class.deserialize(data)
            task.to_canceled()
            return task

    def execute(self, task):
        """
        Given a task instance, this runs it.

        This includes handling retries & re-raising exceptions.

        Ex::

            task = Task(async=False, retries=5)
            task.to_call(add, 101, 35)
            finished_task = gator.execute(task)

        :param task_id: The identifier of the task to process
        :type task_id: string

        :returns: The completed ``Task`` instance
        """
        try:
            return task.run()
        except Exception:
            if task.retries > 0:
                task.retries -= 1
                task.to_retrying()

                if task.async:
                    # Place it back on the queue.
                    data = task.serialize()
                    task.task_id = self.backend.push(
                        self.queue_name,
                        task.task_id,
                        data
                    )
                else:
                    return self.execute(task)
            else:
                raise

    def task(self, func, *args, **kwargs):
        """
        Pushes a task onto the queue.

        This will instantiate a ``Gator.task_class`` instance, configure
        the callable & its arguments, then push it onto the queue.

        You'll typically want to use either this method or the ``Gator.options``
        context manager (if you need to configure the ``Task`` arguments, such
        as retries, async, task_id, etc.)

        Ex::

            on_queue = gator.task(increment, incr_by=2)

        :param func: The callable with business logic to execute
        :type func: callable

        :param args: Positional arguments to pass to the callable task
        :type args: list

        :param kwargs: Keyword arguments to pass to the callable task
        :type kwargs: dict

        :returns: The ``Task`` instance
        """
        task = self.task_class()
        return self.push(task, func, *args, **kwargs)

    def options(self, **kwargs):
        """
        Allows specifying advanced ``Task`` options to control how the task
        runs.

        This returns a context manager which will create ``Task`` instances
        with the supplied options. See ``Task.__init__`` for the available
        arguments.

        Ex::

            def party_time(task, result):
                # Throw a party in honor of this task completing.
                # ...

            with gator.options(retries=2, on_success=party_time) as opts:
                opts.task(increment, incr_by=2678)

        :param kwargs: Keyword arguments to control the task execution
        :type kwargs: dict

        :returns: An ``Options`` context manager instance
        """
        return Options(self, **kwargs)


class Options(object):
    def __init__(self, gator, **kwargs):
        """
        A context manager for specifying task execution options.

        Typically, you'd use ``Gator.options``, which creates this context
        manager for you. You probably don't want to directly use this.

        :param gator: A configured ``Gator`` instance.
        :type gator: ``Gator`` instance

        :param **kwargs: Keyword arguments to control the task execution
        :type **kwargs: dict
        """
        self.gator = gator
        self.task_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def task(self, func, *args, **kwargs):
        """
        Pushes a task onto the queue (with the specified options).

        This will instantiate a ``Gator.task_class`` instance, configure the
        task execution options, configure the callable & its arguments, then
        push it onto the queue.

        You'll typically call this method when specifying advanced options.

        :param func: The callable with business logic to execute
        :type func: callable

        :param args: Positional arguments to pass to the callable task
        :type args: list

        :param kwargs: Keyword arguments to pass to the callable task
        :type kwargs: dict

        :returns: The ``Task`` instance
        """
        task = self.gator.task_class(**self.task_kwargs)
        return self.gator.push(task, func, *args, **kwargs)
