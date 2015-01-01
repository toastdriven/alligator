class Client(object):
    queues = {}
    task_data = {}

    def __init__(self, conn_string):
        """
        An in-memory ``Client``. Useful for development & testing.

        Likely not particularly thread-safe.

        :param conn_string: The DSN. Ignored.
        :type conn_string: string
        """
        # We ignore the conn_string, since everything is happening in-memory.
        pass

    def len(self, queue_name):
        """
        Returns the length of the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :returns: The length of the queue
        :rtype: integer
        """
        return len(self.__class__.queues.get(queue_name, []))

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string
        """
        cls = self.__class__

        for task_id in cls.queues.get(queue_name, []):
            cls.task_data.pop(task_id, None)

        cls.queues[queue_name] = []

    def push(self, queue_name, task_id, data):
        """
        Pushes a task onto the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :param task_id: The identifier of the task.
        :type task_id: string

        :param data: The relevant data for the task.
        :type data: string
        """
        cls = self.__class__
        cls.queues.setdefault(queue_name, [])
        cls.queues[queue_name].append(task_id)
        cls.task_data[task_id] = data
        return task_id

    def pop(self, queue_name):
        """
        Pops a task off the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :returns: The data for the task.
        :rtype: string
        """
        cls = self.__class__
        queue = cls.queues.get(queue_name, [])

        if queue:
            task_id = queue.pop(0)
            return cls.task_data.pop(task_id, None)

    def get(self, queue_name, task_id):
        """
        Pops a specific task off the queue by identifier.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :param task_id: The identifier of the task.
        :type task_id: string

        :returns: The data for the task.
        :rtype: string
        """
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
