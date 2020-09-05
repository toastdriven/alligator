import os
import unittest
from unittest import mock

from alligator.backends.locmem_backend import Client as LocmemClient


CONN_STRING = os.environ.get("ALLIGATOR_CONN")


@unittest.skipIf(
    not CONN_STRING.startswith("locmem:"), "Skipping Locmem tests"
)
class LocmemTestCase(unittest.TestCase):
    def setUp(self):
        super(LocmemTestCase, self).setUp()
        self.backend = LocmemClient(CONN_STRING)

        # Just reach in & clear things out.
        LocmemClient.queues = {}
        LocmemClient.task_data = {}

    def test_init(self):
        self.assertEqual(LocmemClient.queues, {})
        self.assertEqual(LocmemClient.task_data, {})

    def test_len(self):
        LocmemClient.queues = {
            "all": [["a", None], ["b", 12345678], ["c", None]]
        }
        self.assertEqual(self.backend.len("all"), 3)
        self.assertEqual(self.backend.len("something"), 0)

    def test_drop_all(self):
        LocmemClient.queues = {
            "all": [["a", None], ["b", 12345678], ["c", None]]
        }
        LocmemClient.task_data = {
            "a": {"whatev": True},
            "b": "grump",
            "d": "another",
        }

        self.backend.drop_all("all")
        self.assertEqual(LocmemClient.queues, {"all": []})
        self.assertEqual(LocmemClient.task_data, {"d": "another"})

    def test_push(self):
        self.assertEqual(LocmemClient.queues, {})
        self.assertEqual(LocmemClient.task_data, {})

        self.backend.push("all", "hello", {"whee": 1})
        self.assertEqual(LocmemClient.queues, {"all": [["hello", None]]})
        self.assertEqual(LocmemClient.task_data, {"hello": {"whee": 1}})

    def test_push_delayed(self):
        self.assertEqual(LocmemClient.queues, {})
        self.assertEqual(LocmemClient.task_data, {})

        self.backend.push("all", "hello", {"whee": 1}, delay_until=12345798)
        self.assertEqual(LocmemClient.queues, {"all": [["hello", 12345798]]})
        self.assertEqual(LocmemClient.task_data, {"hello": {"whee": 1}})

    def test_pop(self):
        self.backend.push("all", "hello", {"whee": 1})

        data = self.backend.pop("all")
        self.assertEqual(data, {"whee": 1})
        self.assertEqual(LocmemClient.queues, {"all": []})
        self.assertEqual(LocmemClient.task_data, {})

    @mock.patch("time.time")
    def test_pop_skip_delayed(self, mock_time):
        mock_time.return_value = 12345678

        self.backend.push("all", "hello", {"whee": 1}, delay_until=12345798)
        self.backend.push("all", "hallo", {"whoo": 2})

        # Here, we're checking to make sure a task that's waiting for a
        # "future" time isn't pulled off the queue.
        data = self.backend.pop("all")
        self.assertEqual(data, {"whoo": 2})
        self.assertEqual(LocmemClient.queues, {"all": [["hello", 12345798]]})
        self.assertEqual(LocmemClient.task_data, {"hello": {"whee": 1}})

    def test_get(self):
        self.backend.push("all", "hello", {"whee": 1})
        self.backend.push("all", "world", {"whee": 2})

        data = self.backend.get("all", "world")
        self.assertEqual(data, {"whee": 2})
        self.assertEqual(LocmemClient.queues, {"all": [["hello", None]]})
        self.assertEqual(LocmemClient.task_data, {"hello": {"whee": 1}})

        # Try a non-existent one.
        data = self.backend.get("all", "nopenopenope")
        self.assertEqual(data, None)
