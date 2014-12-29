from .constants import ALL
from .tasks import Task
from .utils import import_attr


class Gator(object):
    def __init__(self, conn_string, queue_name=ALL, task_class=Task, backend_class=None):
        self.conn_string = conn_string
        self.queue_name = queue_name
        self.task_class = task_class
        self.backend_class = backend_class

        if not backend_class:
            self.backend = self.build_backend(self.conn_string)
        else:
            self.backend = backend_class(self.conn_string)

    def build_backend(self, conn_string):
        backend_name, _ = conn_string.split(':', 1)
        backend_path = 'alligator.backends.{}_backend'.format(backend_name)
        client_class = import_attr(backend_path, 'Client')
        return client_class(conn_string)

    def push(self, task, func, *args, **kwargs):
        task.to_call(func, *args, **kwargs)
        data = task.serialize()

        if task.async:
            self.backend.push(self.queue_name, task.task_id, data)
        else:
            self.execute(task)

        return task

    def pop(self):
        data = self.backend.pop(self.queue_name)

        if data:
            task = self.task_class.deserialize(data)
            return self.execute(task)

    def get(self, task_id):
        data = self.backend.get(self.queue_name, task_id)

        if data:
            task = self.task_class.deserialize(data)
            return self.execute(task)

    def execute(self, task):
        try:
            return task.run()
        except Exception:
            if task.retries > 0:
                task.retries -= 1

                if task.async:
                    # Place it back on the queue.
                    data = task.serialize()
                    self.backend.push(self.queue_name, task.task_id, data)
                else:
                    return self.execute(task)
            else:
                raise

    def task(self, func, *args, **kwargs):
        task = self.task_class()
        return self.push(task, func, *args, **kwargs)

    def options(self, **kwargs):
        return Options(self, **kwargs)


class Options(object):
    def __init__(self, gator, **kwargs):
        self.gator = gator
        self.task_kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def task(self, func, *args, **kwargs):
        task = self.gator.task_class(**self.task_kwargs)
        return self.gator.push(task, func, *args, **kwargs)
