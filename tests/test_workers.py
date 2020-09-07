import os
import unittest
from unittest import mock

from alligator.gator import Gator
from alligator.workers import Worker


ALLOW_SLOW = bool(os.environ.get("ALLIGATOR_SLOW", False))
CONN_STRING = os.environ.get("ALLIGATOR_CONN")
FILENAME = "/tmp/alligator_test_workers.txt"


def touch_file():
    with open(FILENAME, "w") as write_file:
        write_file.write("0")


def read_file():
    with open(FILENAME, "r") as read_file:
        return int(read_file.read().strip())


def incr_file(incr):
    value = read_file()

    with open(FILENAME, "w") as write_file:
        value += incr
        write_file.write(str(value))


def rm_file():
    try:
        os.unlink(FILENAME)
    except OSError:
        pass


def raise_error(val):
    raise ValueError("You've chosen... poorly.")


@unittest.skipIf(not ALLOW_SLOW, "Skipping slow worker tests")
class WorkerTestCase(unittest.TestCase):
    def setUp(self):
        super(WorkerTestCase, self).setUp()
        self.gator = Gator("locmem://")
        self.worker = Worker(self.gator, max_tasks=2, nap_time=1)

        self.gator.backend.drop_all("all")
        rm_file()
        touch_file()

    def test_init(self):
        self.assertEqual(self.worker.gator, self.gator)
        self.assertEqual(self.worker.max_tasks, 2)
        self.assertEqual(self.worker.to_consume, "all")
        self.assertEqual(self.worker.nap_time, 1)
        self.assertEqual(self.worker.tasks_complete, 0)

    def test_ident(self):
        ident = self.worker.ident()
        self.assertTrue(ident.startswith("Alligator Worker (#"))

    def test_check_and_run_task(self):
        self.assertEqual(read_file(), 0)

        self.gator.task(incr_file, 2)
        self.gator.task(incr_file, 3)

        self.assertEqual(self.gator.backend.len("all"), 2)
        self.assertEqual(self.worker.tasks_complete, 0)

        self.worker.check_and_run_task()

        self.assertEqual(self.gator.backend.len("all"), 1)
        self.assertEqual(self.worker.tasks_complete, 1)
        self.assertEqual(read_file(), 2)

    def test_check_and_run_task_trap_exception(self):
        self.assertEqual(read_file(), 0)

        self.gator.task(incr_file, 2)
        self.gator.task(incr_file, 3)
        self.gator.task(raise_error, 75)
        self.gator.task(incr_file, 4)

        self.assertEqual(self.gator.backend.len("all"), 4)
        self.assertEqual(self.worker.tasks_complete, 0)

        with mock.patch.object(
            self.worker.log, "exception"
        ) as mock_exception:
            self.assertTrue(self.worker.check_and_run_task())
            self.assertTrue(self.worker.check_and_run_task())

            # Here, it should hit the exception BUT not stop execution.
            self.assertFalse(self.worker.check_and_run_task())

            self.assertTrue(self.worker.check_and_run_task())

            # Make sure we tried to log that exception.
            mock_exception.called_once()

        self.assertEqual(self.gator.backend.len("all"), 0)
        self.assertEqual(self.worker.tasks_complete, 3)
        self.assertEqual(read_file(), 9)

    def test_run_forever(self):
        self.assertEqual(read_file(), 0)

        self.gator.task(incr_file, 2)
        self.gator.task(incr_file, 3)
        self.gator.task(incr_file, 4)

        self.assertEqual(self.gator.backend.len("all"), 3)

        # Should actually only run for two of the three tasks.
        self.worker.run_forever()

        self.assertEqual(self.gator.backend.len("all"), 1)
        self.assertEqual(read_file(), 5)
