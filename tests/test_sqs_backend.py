import os
import time
import unittest


CONN_STRING = os.environ.get("ALLIGATOR_CONN")


@unittest.skipIf(not CONN_STRING.startswith("sqs:"), "Skipping SQS tests")
class SQSTestCase(unittest.TestCase):
    def setUp(self):
        super(SQSTestCase, self).setUp()

        from alligator.backends.sqs_backend import Client as SQSClient

        self.backend = SQSClient(CONN_STRING)

    def test_all(self):
        # Just reach in & clear things out.
        # This sucks, but is an AWS requirement (only once every 60 seconds).
        self.backend.drop_all("all")
        time.sleep(61)

        self.assertEqual(self.backend.conn_string, CONN_STRING)

        self.assertEqual(self.backend.len("all"), 0)
        self.assertEqual(self.backend.len("something"), 0)

        self.backend.push("all", "hello", '{"whee": 1}')
        time.sleep(30)
        self.assertEqual(self.backend.len("all"), 1)

        self.backend.push("all", "hello", '{"whee": 2}')
        time.sleep(30)
        self.assertEqual(self.backend.len("all"), 2)

        data = self.backend.pop("all")
        self.assertEqual(data, '{"whee": 1}')
        time.sleep(30)
        self.assertEqual(self.backend.len("all"), 1)

        with self.assertRaises(NotImplementedError):
            self.backend.get("all", "world")

        # Push a delayed task.
        self.backend.push(
            "all", "hello", '{"whee": 2}', delay_until=9999999999
        )
        time.sleep(30)
        self.assertEqual(self.backend.len("all"), 2)

        self.backend.drop_all("all")
        time.sleep(61)
