import time
from urllib.parse import urlparse

import boto3
from botocore.config import Config


class Client(object):
    def __init__(self, conn_string):
        """
        A Amazon SQS-based ``Client``.

        Args:
            conn_string (str): The DSN. The region is parsed out of it.
                Should be of the format ``sqs://region-name/``
        """
        self.conn_string = conn_string
        bits = urlparse(self.conn_string)
        self.conn = self.get_connection(region=bits.hostname)
        self._queue = None

    def get_connection(self, region):
        """
        Returns a ``SQSConnection`` connection instance.
        """
        config = Config(region_name=region)
        return boto3.resource("sqs", config=config)

    def _get_queue(self, queue_name):
        if self._queue is None:
            self._queue = self.conn.get_queue_by_name(QueueName=queue_name)

        return self._queue

    def len(self, queue_name):
        """
        Returns the length of the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.

        Returns:
            int: The length of the queue
        """
        queue = self._get_queue(queue_name)
        queue.load()
        return int(queue.attributes.get("ApproximateNumberOfMessages", 0))

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.
        """
        queue = self._get_queue(queue_name)
        queue.purge()

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
        kwargs = {
            "MessageBody": data,
        }

        if delay_until is not None:
            now = time.time()
            delay_by = delay_until - now

            if delay_by > 0:
                kwargs["DelaySeconds"] = int(delay_by)

        # SQS doesn't let you specify a task id.
        queue = self._get_queue(queue_name)
        res = queue.send_message(**kwargs)
        return res.get("MessageId")

    def pop(self, queue_name):
        """
        Pops a task off the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.

        Returns:
            str: The data for the task.
        """
        queue = self._get_queue(queue_name)
        messages = queue.receive_messages(MaxNumberOfMessages=1)

        if messages:
            message = messages[0]
            data = message.body
            message.delete()
            return data

    def get(self, queue_name, task_id):
        """
        Unsupported, as SQS does not include this functionality.
        """
        raise NotImplementedError(
            "SQS does not support fetching a specific message off the queue."
        )
