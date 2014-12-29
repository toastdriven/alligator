import json
import uuid

from .constants import WAITING, SUCCESS, FAILED
from .utils import determine_module, determine_name, import_attr


class Task(object):
    def __init__(
        self, task_id=None, retries=0, async=True, on_start=None,
        on_success=None, on_error=None, depends_on=None
    ):
        self.task_id = task_id
        self.retries = int(retries)
        self.async = async
        self.status = WAITING
        self.on_start = on_start
        self.on_success = on_success
        self.on_error = on_error
        self.depends_on = depends_on

        self.func = None
        self.func_args = []
        self.func_kwargs = {}

        if self.task_id is None:
            self.task_id = str(uuid.uuid4())

    def to_call(self, func, *args, **kwargs):
        self.func = func
        self.func_args = args
        self.func_kwargs = kwargs

    def to_waiting(self):
        self.status = WAITING

    def to_success(self):
        self.status = SUCCESS

    def to_failed(self):
        self.status = FAILED

    def serialize(self):
        data = {
            'task_id': self.task_id,
            'retries': self.retries,
            'async': self.async,
            'module': determine_module(self.func),
            'callable': determine_name(self.func),
            'args': self.func_args,
            'kwargs': self.func_kwargs,
            'options': {},
        }

        if self.on_start:
            data['options']['on_start'] = {
                'module': determine_module(self.on_start),
                'callable': determine_name(self.on_start),
            }

        if self.on_success:
            data['options']['on_success'] = {
                'module': determine_module(self.on_success),
                'callable': determine_name(self.on_success),
            }

        if self.on_error:
            data['options']['on_error'] = {
                'module': determine_module(self.on_error),
                'callable': determine_name(self.on_error),
            }

        return json.dumps(data)

    @classmethod
    def deserialize(cls, data):
        data = json.loads(data)
        options = data.get('options', {})

        task = cls(
            task_id=data['task_id'],
            retries=data['retries'],
            async=data['async']
        )

        func = import_attr(data['module'], data['callable'])
        task.to_call(func, *data.get('args', []), **data.get('kwargs', {}))

        if options.get('on_start'):
            task.on_start = import_attr(
                options['on_start']['module'],
                options['on_start']['callable']
            )

        if options.get('on_success'):
            task.on_success = import_attr(
                options['on_success']['module'],
                options['on_success']['callable']
            )

        if options.get('on_error'):
            task.on_error = import_attr(
                options['on_error']['module'],
                options['on_error']['callable']
            )

        return task

    def run(self):
        if self.on_start:
            self.on_start(self)

        try:
            result = self.func(*self.func_args, **self.func_kwargs)
        except Exception as err:
            self.status = FAILED

            if self.on_error:
                self.on_error(self, err)

            raise

        self.status = SUCCESS

        if self.on_success:
            self.on_success(self, result)

        return result
