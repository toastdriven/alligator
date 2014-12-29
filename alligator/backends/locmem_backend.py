class Client(object):
    queues = {}
    task_data = {}

    def __init__(self, conn_string):
        # We ignore the conn_string, since everything is happening in-memory.
        pass

    def len(self, queue_name):
        return len(self.__class__.queues.get(queue_name, []))

    def drop_all(self, queue_name):
        cls = self.__class__

        for task_id in cls.queues.get(queue_name, []):
            cls.task_data.pop(task_id, None)

        cls.queues[queue_name] = []

    def push(self, queue_name, task_id, data):
        cls = self.__class__
        cls.queues.setdefault(queue_name, [])
        cls.queues[queue_name].append(task_id)
        cls.task_data[task_id] = data

    def pop(self, queue_name):
        cls = self.__class__
        queue = cls.queues.get(queue_name, [])

        if queue:
            task_id = queue.pop(0)
            return cls.task_data.pop(task_id, None)

    def get(self, queue_name, task_id):
        # This method is *very* non-thread-safe.
        cls = self.__class__
        queue = cls.queues.get(queue_name, [])

        if queue:
            try:
                offset = queue.index(task_id)
            except ValueError:
                return None

            queue.pop(offset)
            return cls.task_data.pop(task_id, None)
