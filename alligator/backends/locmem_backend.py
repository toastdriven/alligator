import math
import time


class Client(object):
    queues = {}
    task_data = {}

    def __init__(self, conn_string):
        """
        An in-memory `Client`. Useful for development & testing.

        Likely not particularly thread-safe.

        Args:
            conn_string (str): The DSN. Ignored.
        """
        # We ignore the conn_string, since everything is happening in-memory.
        pass

    def len(self, queue_name):
        """
        Returns the length of the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                `Gator` instance.

        Returns:
            int: The length of the queue
        """
        return len(self.__class__.queues.get(queue_name, []))

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                `Gator` instance.
        """
        cls = self.__class__

        for task_id, _ in cls.queues.get(queue_name, []):
            cls.task_data.pop(task_id, None)

        cls.queues[queue_name] = []

    def push(self, queue_name, task_id, data, delay_until=None):
        """
        Pushes a task onto the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                `Gator` instance.
            task_id (str): The identifier of the task.
            data (str): The relevant data for the task.
            delay_until (float): Optional. The Unix timestamp to delay
                execution of the task until. Default is `None` (no delay).

        Returns:
            str: The task's ID
        """
        cls = self.__class__
        cls.queues.setdefault(queue_name, [])
        cls.queues[queue_name].append([task_id, delay_until])
        cls.task_data[task_id] = data
        return task_id

    def pop(self, queue_name):
        """
        Pops a task off the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                `Gator` instance.

        Returns:
            str: The data for the task.
        """
        cls = self.__class__
        queue = cls.queues.get(queue_name, [])
        now = math.floor(time.time())

        for offset, task_info in enumerate(queue):
            task_id, delay_until = task_info[0], task_info[1]

            # Check for a delay.
            if delay_until is not None:
                if now < delay_until:
                    continue

            # We've found one we can process.
            queue.pop(offset)
            return cls.task_data.pop(task_id, None)

    def get(self, queue_name, task_id):
        """
        Pops a specific task off the queue by identifier.

        Args:
            queue_name: The name of the queue. Usually handled by the
                `Gator` instance.
            task_id (str): The identifier of the task.

        Returns:
            str: The data for the task.
        """
        # This method is *very* non-thread-safe.
        cls = self.__class__
        queue = cls.queues.get(queue_name, [])

        for offset, task_info in enumerate(queue):
            if task_info[0] == task_id:
                queue.pop(offset)
                return cls.task_data.pop(task_id, None)
