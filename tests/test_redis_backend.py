import os
import redis
import unittest

from alligator.backends.redis_backend import Client as RedisClient


CONN_STRING = os.environ.get("ALLIGATOR_CONN")


@unittest.skipIf(not CONN_STRING.startswith("redis:"), "Skipping Redis tests")
class RedisTestCase(unittest.TestCase):
    def setUp(self):
        super(RedisTestCase, self).setUp()
        self.backend = RedisClient(CONN_STRING)

        # Just reach in & clear things out.
        self.backend.conn.flushdb()

    def test_init(self):
        self.assertEqual(self.backend.conn_string, CONN_STRING)
        self.assertTrue(isinstance(self.backend.conn, redis.StrictRedis))

    def test_len(self):
        self.assertEqual(self.backend.len("all"), 0)
        self.assertEqual(self.backend.len("something"), 0)

    def test_drop_all(self):
        self.backend.push("all", "hello", '{"whee": 1}')
        self.backend.push("all", "world", '{"whee": 2}')

        self.assertEqual(self.backend.len("all"), 2)
        self.backend.drop_all("all")
        self.assertEqual(self.backend.len("all"), 0)

    def test_push(self):
        self.assertEqual(self.backend.len("all"), 0)

        self.backend.push("all", "hello", '{"whee": 1}')
        self.assertEqual(self.backend.len("all"), 1)

    def test_pop(self):
        self.backend.push("all", "hello", '{"whee": 1}')

        data = self.backend.pop("all")
        self.assertEqual(data, '{"whee": 1}')
        self.assertEqual(self.backend.len("all"), 0)

    def test_get(self):
        self.backend.push("all", "hello", '{"whee": 1}')
        self.backend.push("all", "world", '{"whee": 2}')

        data = self.backend.get("all", "world")
        self.assertEqual(data, '{"whee": 2}')
        self.assertEqual(self.backend.len("all"), 1)
