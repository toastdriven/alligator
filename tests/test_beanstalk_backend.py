import os
import sys
import unittest


# Test if we're Python 3, which beanstalkc doesn't support. :(
PY2 = sys.version_info[0] == 2
CONN_STRING = os.environ.get('ALLIGATOR_CONN')


@unittest.skipIf(
    not PY2,
    'Skipping Beanstalk tests due to Python 3'
)
@unittest.skipIf(
    not CONN_STRING.startswith('beanstalk:'),
    'Skipping Beanstalk tests'
)
class BeanstalkTestCase(unittest.TestCase):
    def setUp(self):
        super(BeanstalkTestCase, self).setUp()

        from alligator.backends.beanstalk_backend import Client as BeanstalkClient
        self.backend = BeanstalkClient(CONN_STRING)

        # Just reach in & clear things out.
        self.backend.drop_all('all')

    def test_init(self):
        self.assertEqual(self.backend.conn_string, CONN_STRING)

    def test_len(self):
        self.assertEqual(self.backend.len('all'), 0)
        self.assertEqual(self.backend.len('something'), 0)

    def test_drop_all(self):
        self.backend.push('all', 'hello', "{'whee': 1}")
        self.backend.push('all', 'world', "{'whee': 1}")

        self.assertEqual(self.backend.len('all'), 2)
        self.backend.drop_all('all')
        self.assertEqual(self.backend.len('all'), 0)

    def test_push(self):
        self.assertEqual(self.backend.len('all'), 0)

        self.backend.push('all', 'hello', "{'whee': 1}")
        self.assertEqual(self.backend.len('all'), 1)

    def test_pop(self):
        self.backend.push('all', 'hello', "{'whee': 1}")

        data = self.backend.pop('all')
        self.assertEqual(data, "{'whee': 1}")
        self.assertEqual(self.backend.len('all'), 0)

    def test_get(self):
        jid_1 = self.backend.push('all', 'hello', "{'whee': 1}")
        jid_2 = self.backend.push('all', 'world', "{'whee': 2}")

        data = self.backend.get('all', jid_2)
        self.assertEqual(data, "{'whee': 2}")
        self.assertEqual(self.backend.len('all'), 1)
