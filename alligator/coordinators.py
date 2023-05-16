import asyncio
import multiprocessing
import os

from alligator import daemons


class Coordinator(daemons.Daemon):
    def __init__(self, gator, pool_size=None, **kwargs):
        """
        An object for consuming the queue & running the tasks.

        Ex::

            from alligator import Gator, Coordinator

            gator = Gator('locmem://')
            coord = Coordinator(gator)
            coord.run_forever()

        Args:
            gator (Gator): A configured ``Gator`` object
            max_tasks (int): Optional. The maximum number of tasks to consume.
                Useful if you're concerned about memory leaks or want
                short-lived workers. Defaults to ``0`` (unlimited tasks).
            to_consume (str): Optional. The queue name the worker should
                consume from. Defaults to ``ALL``.
            nap_time (float): Optional. To prevent high CPU usage in the busy
                loop, you can specify a time delay (in seconds) between
                tasks. Set to ``0`` to disable sleep & consume as fast as
                possible. Defaults to ``0.1``.
            log_level (int): Optional. The logging level you'd like for
                output. Default is ``logging.INFO``.
        """
        super().__init__(gator, **kwargs)
        self._pool = {}
        self.pool_size = pool_size
        self._stats = {
            "tasks_processed": 0,
        }

    def ident(self):
        """
        Returns a string identifier for the coordinator.

        Used in the printed messages & includes the process ID.
        """
        return "Alligator Coordinator (#{})".format(os.getpid())

    def starting(self):
        """
        Prints a startup message to stdout.
        """
        super().starting()
        ident = self.ident()

        if self.max_tasks:
            self.log.info(
                "{} will die after {} tasks.".format(ident, self.max_tasks)
            )
        else:
            self.log.info("{} will never die.".format(ident))

    def result(self, result):
        """
        Prints the received result from a task to stdout.

        Args:
            result (Any): The result of the task
        """
        if result is not None:
            self.log.info(result)

    def busy_loop(self):
        """
        Handles the logic of checking for & executing a task.

        `Worker.run_forever` uses this in a loop to actually handle the main
        logic, though you can call this on your own if you have different
        needs.

        Returns:
            bool: `True` if a task was run successfully, `False` if there was
                no task to process or executing the task failed.
        """
        if self.max_tasks and self.tasks_complete >= self.max_tasks:
            raise daemons.StopBusyLoop()

        if self.gator.len():
            try:
                task = self.gator.pop(execute=False)

                # FIXME: Pass the task off to a child worker.
            except Exception as err:
                self.log.exception(err)
                return False

            if task is None:
                return False

            self.tasks_complete += 1
            self.result(task.result)
            return True

        return False
