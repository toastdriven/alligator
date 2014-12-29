import os
import unittest

from alligator.backends.locmem_backend import Client as LocmemClient
from alligator.backends.redis_backend import Client as RedisClient
from alligator.constants import ALL
from alligator.gator import Gator, Options
from alligator.tasks import Task


class CustomTask(Task):
    pass


class CustomClient(LocmemClient):
    pass


def so_computationally_expensive(initial, incr):
    return initial + incr


def fail_task(initial, incr):
    raise IOError('Math is hard.')


def eventual_success():
    data = {'count': 0}

    def wrapped(initial, incr):
        data['count'] += 1

        if data['count'] < 3:
            raise IOError('Nope.')

        return initial + incr

    return wrapped


class GatorTestCase(unittest.TestCase):
    def setUp(self):
        super(GatorTestCase, self).setUp()
        self.conn_string = os.environ.get('ALLIGATOR_CONN')
        self.gator = Gator(self.conn_string)

        # Just reach in & clear things out.
        self.gator.backend.drop_all(ALL)

    def test_init(self):
        gator = Gator('whatever://', backend_class=CustomClient)
        self.assertEqual(gator.conn_string, 'whatever://')
        self.assertEqual(gator.queue_name, ALL)
        self.assertEqual(gator.task_class, Task)
        self.assertEqual(gator.backend_class, CustomClient)
        self.assertTrue(isinstance(gator.backend, CustomClient))

        gator = Gator(
            'locmem://',
            queue_name='hard_things',
            task_class=CustomTask
        )
        self.assertEqual(gator.conn_string, 'locmem://')
        self.assertEqual(gator.queue_name, 'hard_things')
        self.assertEqual(gator.task_class, CustomTask)
        self.assertEqual(gator.backend_class, None)
        self.assertTrue(isinstance(gator.backend, LocmemClient))

    def test_build_backend(self):
        backend = self.gator.build_backend('locmem://')
        self.assertTrue(isinstance(backend, LocmemClient))

        backend = self.gator.build_backend('redis://localhost:6379/0')
        self.assertTrue(isinstance(backend, RedisClient))

    def test_push_async(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        task = Task(async=True)
        self.gator.push(task, so_computationally_expensive, 1, 1)
        self.assertEqual(self.gator.backend.len(ALL), 1)

    def test_push_sync(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        def success(t, result):
            t.result = result

        task = Task(async=False, on_success=success)
        res = self.gator.push(task, so_computationally_expensive, 1, 1)
        self.assertEqual(self.gator.backend.len(ALL), 0)
        self.assertEqual(res.result, 2)

    def test_pop(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        task = Task(async=True)
        self.gator.push(task, so_computationally_expensive, 1, 1)
        self.assertEqual(self.gator.backend.len(ALL), 1)

        res = self.gator.pop()
        self.assertEqual(res, 2)

    def test_get(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        task_1 = Task(async=True)
        task_2 = Task(task_id='hello', async=True)
        self.gator.push(task_1, so_computationally_expensive, 1, 1)
        self.gator.push(task_2, so_computationally_expensive, 3, 5)
        self.assertEqual(self.gator.backend.len(ALL), 2)

        res = self.gator.get('hello')
        self.assertEqual(res, 8)

        res = self.gator.get(task_1.task_id)
        self.assertEqual(res, 2)

    def test_execute_success(self):
        task = Task(retries=3, async=True)
        task.to_call(so_computationally_expensive, 2, 7)

        res = self.gator.execute(task)
        self.assertEqual(res, 9)
        self.assertEqual(task.retries, 3)

    def test_execute_failed(self):
        task = Task(retries=3, async=True)
        task.to_call(fail_task, 2, 7)

        try:
            self.gator.execute(task)
            self.gator.execute(task)
            self.gator.execute(task)
            self.gator.execute(task)
            self.fail()
        except IOError:
            self.assertEqual(task.retries, 0)

    def test_execute_retries(self):
        task = Task(retries=3, async=True)
        task.to_call(eventual_success(), 2, 7)

        try:
            self.gator.execute(task)
        except IOError:
            pass

        try:
            self.gator.execute(task)
        except IOError:
            pass

        res = self.gator.execute(task)
        self.assertEqual(res, 9)
        self.assertEqual(task.retries, 1)

    def test_task(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        self.gator.task(so_computationally_expensive, 1, 1)
        self.assertEqual(self.gator.backend.len(ALL), 1)

    def test_options(self):
        self.assertEqual(self.gator.backend.len(ALL), 0)

        def success(t, result):
            t.result = result

        with self.gator.options(retries=4, async=False, on_success=success) as opts:
            res = opts.task(eventual_success(), 3, 9)

        self.assertEqual(res.retries, 2)
        self.assertEqual(res.result, 12)
