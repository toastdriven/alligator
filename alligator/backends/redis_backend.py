import math
import time
from urllib.parse import urlparse

import redis


class Client(object):
    def __init__(self, conn_string):
        """
        A Redis-based ``Client``.

        Args:
            conn_string (str): The DSN. The host/port/db are parsed out of it.
                Should be of the format ``redis://host:port/db``
        """
        self.conn_string = conn_string
        bits = urlparse(self.conn_string)
        self.conn = self.get_connection(
            host=bits.hostname,
            port=bits.port,
            db=bits.path.lstrip("/").split("/")[0],
        )

    def get_connection(self, host, port, db):
        """
        Returns a ``StrictRedis`` connection instance.
        """
        return redis.StrictRedis(
            host=host, port=port, db=db, decode_responses=True
        )

    def len(self, queue_name):
        """
        Returns the length of the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                `Gator`` instance.

        Returns:
            int: The length of the queue
        """
        return self.conn.zcard(queue_name)

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.
        """
        task_ids = self.conn.zrange(queue_name, 0, -1)

        for task_id in task_ids:
            self.conn.delete(task_id)

        self.conn.delete(queue_name)

    def push(self, queue_name, task_id, data, delay_until=None):
        """
        Pushes a task onto the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.
            task_id (str): The identifier of the task.
            data (str): The relevant data for the task.
            delay_until (float): Optional. The Unix timestamp to delay
                processing of the task until. Default is `None`.

        Returns:
            str: The task ID.
        """
        if delay_until is None:
            delay_until = math.ceil(time.time())

        self.conn.zadd(queue_name, {task_id: delay_until}, nx=True)
        self.conn.set(task_id, data)
        return task_id

    def pop(self, queue_name):
        """
        Pops a task off the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.

        Returns:
            str: The data for the task.
        """
        now = math.floor(time.time())
        available_to_pop = self.conn.zrangebyscore(
            queue_name, 0, now, start=0, num=1
        )

        if not len(available_to_pop):
            return None

        popped = self.conn.zpopmin(queue_name)
        task_id, delay_until = popped[0][0], popped[0][1]
        data = self.conn.get(task_id)
        self.conn.delete(task_id)
        return data

    def get(self, queue_name, task_id):
        """
        Pops a specific task off the queue by identifier.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.
            task_id (str): The identifier of the task.

        Returns:
            str: The data for the task.
        """
        self.conn.zrem(queue_name, task_id)
        data = self.conn.get(task_id)

        if data:
            self.conn.delete(task_id)
            return data
