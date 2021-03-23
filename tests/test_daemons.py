import logging
import os
import unittest
from unittest import mock

from alligator.gator import Gator
from alligator import daemons


ALLOW_SLOW = bool(os.environ.get("ALLIGATOR_SLOW", False))
CONN_STRING = os.environ.get("ALLIGATOR_CONN")
FILENAME = "/tmp/alligator_test_daemons.txt"


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


@unittest.skipIf(not ALLOW_SLOW, "Skipping slow daemon tests")
class DaemonTestCase(unittest.TestCase):
    def setUp(self):
        super(DaemonTestCase, self).setUp()
        self.gator = Gator("locmem://")
        self.daemon = daemons.Daemon(self.gator, nap_time=1)

        self.gator.backend.drop_all("all")
        rm_file()
        touch_file()

    def test_init(self):
        self.assertEqual(self.daemon.gator, self.gator)
        self.assertEqual(self.daemon.to_consume, "all")
        self.assertEqual(self.daemon.nap_time, 1)
        self.assertEqual(self.daemon.keep_running, False)

    def test_get_log(self):
        log = self.daemon.get_log()

        self.assertTrue(isinstance(log, logging.Logger))
        self.assertEqual(log.level, logging.INFO)

    def test_ident(self):
        with self.assertRaises(NotImplementedError):
            self.daemon.ident()

    def test_starting(self):
        self.assertFalse(self.daemon.keep_running)

        with mock.patch.object(self.daemon, "ident") as mock_ident:
            self.daemon.starting()
            self.assertTrue(self.daemon.keep_running)
            mock_ident.assert_called_once()

    def test_interrupt(self):
        self.daemon.keep_running = True
        self.assertTrue(self.daemon.keep_running)

        with mock.patch.object(self.daemon, "ident") as mock_ident:
            self.daemon.interrupt()
            self.assertFalse(self.daemon.keep_running)
            mock_ident.assert_called_once()

    def test_stopping(self):
        self.daemon.keep_running = True
        self.assertTrue(self.daemon.keep_running)

        with mock.patch.object(self.daemon, "ident") as mock_ident:
            self.daemon.stopping()
            self.assertFalse(self.daemon.keep_running)
            mock_ident.assert_called_once()

    def test_busy_loop(self):
        with self.assertRaises(NotImplementedError):
            self.daemon.busy_loop()

    def test_run_forever(self):
        self._counter = 0

        def busy_count():
            if self._counter >= 2:
                raise daemons.StopBusyLoop()

            self._counter += 1

        with mock.patch.object(self.daemon, "ident"):
            with mock.patch.object(
                self.daemon, "busy_loop", side_effect=busy_count
            ) as mock_busy:
                self.daemon.run_forever()

                self.assertEqual(len(mock_busy.call_args), 2)
                self.assertEqual(self._counter, 2)
