import os
import unittest

from alligator.constants import ALL
from alligator.gator import Gator, Options
from alligator.tasks import Task

from .sqlite_backend import Client as SQLiteClient


def add(a, b):
    return a + b


class CustomBackendTestCase(unittest.TestCase):
    def setUp(self):
        super(CustomBackendTestCase, self).setUp()
        self.conn_string = 'sqlite:///tmp/alligator_test.db'

        try:
            os.unlink('/tmp/alligator_test.db')
        except OSError:
            pass

        self.gator = Gator(self.conn_string, backend_class=SQLiteClient)
        self._setup_tables()

    def _setup_tables(self):
        # We're just going to assume ``ALL``.
        query = 'CREATE TABLE `all` (task_id text, data text)'
        self.gator.backend._run_query(query, None)

    def test_everything(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        t1 = self.gator.task(add, 1, 3)
        t2 = self.gator.task(add, 5, 7)
        t3 = self.gator.task(add, 3, 13)
        t4 = self.gator.task(add, 9, 4)

        self.assertEqual(self.gator.backend.len(ALL), 4)

        task_1 = self.gator.pop()
        self.assertEqual(task_1, 4)

        task_3 = self.gator.get(t3.task_id)
        self.assertEqual(task_3, 16)

        task_2 = self.gator.pop()
        self.assertEqual(task_2, 12)

        self.assertEqual(self.gator.backend.len(ALL), 1)

        self.gator.backend.drop_all(ALL)
        self.assertEqual(self.gator.backend.len(ALL), 0)
