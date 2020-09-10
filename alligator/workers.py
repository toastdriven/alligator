import logging
import os
import signal
import time
import traceback

from alligator.constants import ALL


class Worker(object):
    def __init__(
        self,
        gator,
        max_tasks=0,
        to_consume=ALL,
        nap_time=0.1,
        log_level=logging.INFO,
    ):
        """
        An object for consuming the queue & running the tasks.

        Ex::

            from alligator import Gator, Worker

            gator = Gator('locmem://')
            worker = Worker(gator)
            worker.run_forever()

        Args:
            gator (Gator): A configured `Gator` object
            max_tasks (int): Optional. The maximum number of tasks to consume.
                Useful if you're concerned about memory leaks or want
                short-lived workers. Defaults to `0` (unlimited tasks).
            to_consume (str): Optional. The queue name the worker should
                consume from. Defaults to `ALL`.
            nap_time (float): Optional. To prevent high CPU usage in the busy
                loop, you can specify a time delay (in seconds) between
                tasks. Set to `0` to disable sleep & consume as fast as
                possible. Defaults to `0.1`
            log_level (int): Optional. The logging level you'd like for
                output. Default is `logging.INFO`.
        """
        self.gator = gator
        self.max_tasks = int(max_tasks)
        self.to_consume = to_consume
        self.nap_time = nap_time
        self.tasks_complete = 0
        self.keep_running = False
        self.log_level = log_level
        self.log = self.get_log(self.log_level)

    def get_log(self, log_level=logging.INFO):
        """
        Sets up logging for the instance.

        Args:
            log_level (int): Optional. The logging level you'd like for
                output. Default is `logging.INFO`.

        Returns:
            logging.Logger: The log instance.
        """
        log = logging.getLogger(__name__)
        default_format = logging.Formatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(default_format)
        log.addHandler(stdout_handler)
        log.setLevel(logging.INFO)
        return log

    def ident(self):
        """
        Returns a string identifier for the worker.

        Used in the printed messages & includes the process ID.
        """
        return "Alligator Worker (#{})".format(os.getpid())

    def starting(self):
        """
        Prints a startup message to stdout.
        """
        self.keep_running = True
        ident = self.ident()
        self.log.info(
            '{} starting & consuming "{}".'.format(ident, self.to_consume)
        )

        if self.max_tasks:
            self.log.info(
                "{} will die after {} tasks.".format(ident, self.max_tasks)
            )
        else:
            self.log.info("{} will never die.".format(ident))

    def interrupt(self):
        """
        Prints an interrupt message to stdout.
        """
        self.keep_running = False
        ident = self.ident()
        self.log.info(
            '{} for "{}" saw interrupt. Finishing in-progress task.'.format(
                ident, self.to_consume
            )
        )

    def stopping(self):
        """
        Prints a shutdown message to stdout.
        """
        self.keep_running = False
        ident = self.ident()
        self.log.info(
            '{} for "{}" shutting down. Consumed {} tasks.'.format(
                ident, self.to_consume, self.tasks_complete
            )
        )

    def result(self, result):
        """
        Prints the received result from a task to stdout.

        :param result: The result of the task
        """
        if result is not None:
            self.log.info(result)

    def check_and_run_task(self):
        """
        Handles the logic of checking for & executing a task.

        `Worker.run_forever` uses this in a loop to actually handle the main
        logic, though you can call this on your own if you have different
        needs.

        Returns:
            bool: `True` if a task was run successfully, `False` if there was
                no task to process or executing the task failed.
        """
        if self.gator.len():
            try:
                task = self.gator.pop()
            except Exception as err:
                self.log.exception(err)
                return False

            if task is None:
                return False

            self.tasks_complete += 1
            self.result(task.result)
            return True

        return False

    def run_forever(self):
        """
        Causes the worker to run either forever or until the
        `Worker.max_tasks` are reached.
        """
        self.starting()

        def handle(signum, frame):
            self.interrupt()

        signal.signal(signal.SIGINT, handle)

        while self.keep_running:
            if self.max_tasks and self.tasks_complete >= self.max_tasks:
                self.stopping()
                break

            self.check_and_run_task()

            if self.nap_time >= 0:
                time.sleep(self.nap_time)

        return 0
