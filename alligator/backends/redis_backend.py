import math
import time
from urllib.parse import urlparse

import redis


class Client(object):
    def __init__(self, conn_string):
        """
        A Redis-based ``Client``.

        :param conn_string: The DSN. The host/port/db are parsed out of it.
            Should be of the format ``redis://host:port/db``
        :type conn_string: string
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

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :returns: The length of the queue
        :rtype: integer
        """
        return self.conn.zcard(queue_name)

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string
        """
        task_ids = self.conn.zrange(queue_name, 0, -1)

        for task_id in task_ids:
            self.conn.delete(task_id)

        self.conn.delete(queue_name)

    def push(self, queue_name, task_id, data, delay_until=None):
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
        if delay_until is None:
            delay_until = math.ceil(time.time())

        self.conn.zadd(queue_name, {task_id: delay_until}, nx=True)
        self.conn.set(task_id, data)
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
        now = math.floor(time.time())
        available_to_pop = self.conn.zrange(queue_name, 0, now)

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

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :param task_id: The identifier of the task.
        :type task_id: string

        :returns: The data for the task.
        :rtype: string
        """
        self.conn.zrem(queue_name, task_id)
        data = self.conn.get(task_id)

        if data:
            self.conn.delete(task_id)
            return data
