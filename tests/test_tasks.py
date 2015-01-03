import json
import unittest

from alligator.constants import WAITING, SUCCESS, FAILED, RETRYING, CANCELED
from alligator.tasks import Task


def run_me(x, y=None): pass
def start(task): pass
def error(task, err): pass
def success(task, result): pass


class TaskTestCase(unittest.TestCase):
    def setUp(self):
        super(TaskTestCase, self).setUp()
        self.task = Task()

    def test_default_init(self):
        task = Task()
        self.assertNotEqual(task.task_id, None)
        self.assertEqual(task.retries, 0)
        self.assertEqual(task.async, True)
        self.assertEqual(task.on_start, None)
        self.assertEqual(task.on_success, None)
        self.assertEqual(task.on_error, None)
        self.assertEqual(task.depends_on, None)
        self.assertEqual(task.status, WAITING)
        self.assertEqual(task.func, None)
        self.assertEqual(task.func_args, [])
        self.assertEqual(task.func_kwargs, {})

    def test_custom_init(self):
        task = Task(
            task_id='hello',
            retries=3,
            async=False,
            on_start=start,
            on_success=success,
            on_error=error,
            depends_on=['id1', 'id3', 'id4']
        )
        self.assertNotEqual(task.task_id, None)
        self.assertEqual(task.retries, 3)
        self.assertEqual(task.async, False)
        self.assertEqual(task.on_start, start)
        self.assertEqual(task.on_success, success)
        self.assertEqual(task.on_error, error)
        self.assertEqual(task.depends_on, ['id1', 'id3', 'id4'])
        self.assertEqual(task.status, WAITING)
        self.assertEqual(task.func, None)
        self.assertEqual(task.func_args, [])
        self.assertEqual(task.func_kwargs, {})

    def test_to_call(self):
        self.assertEqual(self.task.func, None)
        self.assertEqual(self.task.func_args, [])
        self.assertEqual(self.task.func_kwargs, {})

        self.task.to_call(run_me, 1, y=2)

        self.assertEqual(self.task.func, run_me)
        self.assertEqual(self.task.func_args, (1,))
        self.assertEqual(self.task.func_kwargs, {'y': 2})

    def test_to_waiting(self):
        # This shouldn't normally be done. Better to use ``task.to_success``...
        self.task.status = SUCCESS
        self.assertEqual(self.task.status, SUCCESS)

        self.task.to_waiting()
        self.assertEqual(self.task.status, WAITING)

    def test_to_success(self):
        self.assertEqual(self.task.status, WAITING)

        self.task.to_success()
        self.assertEqual(self.task.status, SUCCESS)

    def test_to_failed(self):
        self.assertEqual(self.task.status, WAITING)

        self.task.to_failed()
        self.assertEqual(self.task.status, FAILED)

    def test_to_canceled(self):
        self.assertEqual(self.task.status, WAITING)

        self.task.to_canceled()
        self.assertEqual(self.task.status, CANCELED)

    def test_to_retrying(self):
        self.assertEqual(self.task.status, WAITING)

        self.task.to_retrying()
        self.assertEqual(self.task.status, RETRYING)

    def test_serialize(self):
        # Shenanigans. You'd normally use the kwargs at ``__init__``...
        self.task.task_id = 'hello'
        self.task.on_success = success

        self.task.to_call(run_me, 1, y=2)
        raw_json = self.task.serialize()

        data = json.loads(raw_json)
        self.assertEqual(data, {
            'task_id': 'hello',
            'retries': 0,
            'async': True,

            'module': 'tests.test_tasks',
            'callable': 'run_me',
            'args': [1],
            'kwargs': {'y': 2},

            'options': {
                'on_success': {
                    'module': 'tests.test_tasks',
                    'callable': 'success',
                }
            },
        })

    def test_deserialize(self):
        raw_json = json.dumps({
            'task_id': 'hello',
            'retries': 3,
            'async': False,

            'module': 'tests.test_tasks',
            'callable': 'run_me',
            'args': [1],
            'kwargs': {'y': 2},

            'options': {
                'on_error': {
                    'module': 'tests.test_tasks',
                    'callable': 'error',
                }
            },
        })
        task = Task.deserialize(raw_json)
        self.assertEqual(task.task_id, 'hello')
        self.assertEqual(task.retries, 3)
        self.assertEqual(task.async, False)
        self.assertEqual(task.on_start, None)
        self.assertEqual(task.on_success, None)
        self.assertEqual(task.on_error, error)
        self.assertEqual(task.depends_on, None)
        self.assertEqual(task.status, WAITING)
        self.assertEqual(task.func, run_me)
        self.assertEqual(task.func_args, (1,))
        self.assertEqual(task.func_kwargs, {'y': 2})

    def test_run_failed(self):
        def start(t):
            t.started = True

        def error(t, err):
            t.err_msg = str(err)

        def success(t, result):
            t.success_result = result

        def fail_task(inital, incr_by=1):
            raise IOError('Math is hard.')

        task = Task(
            on_start=start,
            on_success=success,
            on_error=error
        )

        # Should fail.
        task.to_call(fail_task, 2)

        try:
            task.run()
        except IOError:
            pass

        self.assertTrue(task.started)
        self.assertEqual(task.err_msg, 'Math is hard.')

    def test_run_success(self):
        def start(t):
            t.started = True

        def error(t, err):
            t.err_msg = str(err)

        def success(t, result):
            t.success_result = result

        def success_task(initial, incr_by=1):
            return initial + incr_by

        task = Task(
            on_start=start,
            on_success=success,
            on_error=error
        )

        # Should succeed.
        task.to_call(success_task, 12, 3)
        result = task.run()
        self.assertEqual(result, 15)
        self.assertTrue(task.started)
        self.assertEqual(task.success_result, 15)
