import os
import time
import unittest

from alligator.backends.sqs_backend import Client as SQSClient


CONN_STRING = os.environ.get('ALLIGATOR_CONN')


@unittest.skipIf(not CONN_STRING.startswith('sqs:'), 'Skipping SQS tests')
class SQSTestCase(unittest.TestCase):
    def setUp(self):
        super(SQSTestCase, self).setUp()
        self.backend = SQSClient(CONN_STRING)

        # Just reach in & clear things out.
        # This sucks, but is an AWS requirement (only once every 60 seconds).
        self.backend.drop_all('all')
        time.sleep(61)

    def test_init(self):
        self.assertEqual(self.backend.conn_string, CONN_STRING)

    def test_len(self):
        self.assertEqual(self.backend.len('all'), 0)
        self.assertEqual(self.backend.len('something'), 0)

    # def test_drop_all(self):
    #     self.backend.push('all', 'hello', {'whee': 1})
    #     self.backend.push('all', 'world', {'whee': 2})
    #
    #     self.assertEqual(self.backend.len('all'), 2)
    #     self.backend.drop_all('all')
    #     self.assertEqual(self.backend.len('all'), 0)

    def test_push(self):
        self.assertEqual(self.backend.len('all'), 0)

        self.backend.push('all', 'hello', {'whee': 1})
        self.assertEqual(self.backend.len('all'), 1)

    def test_pop(self):
        self.backend.push('all', 'hello', {'whee': 1})

        data = self.backend.pop('all')
        self.assertEqual(data, "{'whee': 1}")
        self.assertEqual(self.backend.len('all'), 0)

    def test_get(self):
        with self.assertRaises(NotImplementedError):
            self.backend.get('all', 'world')
