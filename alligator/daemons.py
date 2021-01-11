import logging
import signal
import time

from alligator.constants import ALL


class StopBusyLoop(Exception):
    pass


class Daemon(object):
    def __init__(
        self, gator, to_consume=ALL, nap_time=0.1, log_level=logging.INFO,
    ):
        """
        A base object for creating task queue daemons.

        You must subclass this object & implement the following methods:

        * `ident`
        * `busy_loop`

        Ex::

            import os
            from alligator import Daemon

            class SimpleWorker(Daemon):
                def ident(self):
                    return "Worker (#{})".format(os.getpid())

                def busy_loop(self):
                    if self.gator.len():
                        task = self.gator.pop()

                        if task is None:
                            return False

                        self.result(task.result)
                        return True

                    return False

        Args:
            gator (Gator): A configured `Gator` object
            to_consume (str): Optional. The queue name the daemon should
                consume from. Defaults to `ALL`.
            nap_time (float): Optional. To prevent high CPU usage in the busy
                loop, you can specify a time delay (in seconds) between
                tasks. Set to `0` to disable sleep & consume as fast as
                possible. Defaults to `0.1`
            log_level (int): Optional. The logging level you'd like for
                output. Default is `logging.INFO`.
        """
        self.gator = gator
        self.to_consume = to_consume
        self.nap_time = nap_time
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
        Returns a string identifier for the daemon.

        Used in the printed messages & includes the process ID.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def starting(self):
        """
        Prints a startup message to stdout.
        """
        self.keep_running = True
        ident = self.ident()
        self.log.info(
            '{} starting & consuming "{}".'.format(ident, self.to_consume)
        )

    def interrupt(self):
        """
        Prints an interrupt message to stdout.
        """
        self.keep_running = False
        ident = self.ident()
        self.log.info(
            '{} for "{}" saw interrupt. Finishing...'.format(
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
            '{} for "{}" shutting down.'.format(ident, self.to_consume)
        )

    def busy_loop(self):
        """
        Handles the logic of checking for & executing a task.

        `Daemon.run_forever` uses this in a loop to actually handle the main
        logic, though you can call this on your own if you have different
        needs.

        Returns:
            bool: `True` if a task was run successfully, `False` if there was
                no task to process or executing the task failed.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def run_forever(self):
        """
        Causes the daemon to run forever.
        """
        self.starting()

        def handle(signum, frame):
            self.interrupt()

        signal.signal(signal.SIGINT, handle)

        try:
            while self.keep_running:
                self.busy_loop()

                if self.nap_time >= 0:
                    time.sleep(self.nap_time)
        except StopBusyLoop:
            self.stopping()

        return 0
