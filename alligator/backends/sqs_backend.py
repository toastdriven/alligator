import boto.sqs
from boto.sqs.jsonmessage import JSONMessage

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Client(object):
    def __init__(self, conn_string):
        """
        A Amazon SQS-based ``Client``.

        :param conn_string: The DSN. The region is parsed out of it.
            Should be of the format ``sqs://region/``
        :type conn_string: string
        """
        self.conn_string = conn_string
        bits = urlparse(self.conn_string)
        self.conn = self.get_connection(
            region=bits.hostname
        )

    def get_connection(self, region):
        """
        Returns a ``SQSConnection`` connection instance.
        """
        return boto.sqs.connect_to_region(region)

    def _get_queue(self, queue_name):
        queue = self.conn.get_queue(queue_name)
        queue.set_message_class(JSONMessage)
        return queue

    def len(self, queue_name):
        """
        Returns the length of the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :returns: The length of the queue
        :rtype: integer
        """
        queue = self._get_queue(queue_name)
        return queue.count()

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string
        """
        queue = self._get_queue(queue_name)
        queue.purge()

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
        # SQS doesn't let you specify a task id.
        queue = self._get_queue(queue_name)
        message = queue.new_message(body=data)
        queue.write(message)
        return message.id

    def pop(self, queue_name):
        """
        Pops a task off the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :returns: The data for the task.
        :rtype: string
        """
        queue = self._get_queue(queue_name)
        message = queue.read()

        if message:
            data = message.get_body()
            return data

    def get(self, queue_name, task_id):
        """
        Unsupported, as SQS does not include this functionality.
        """
        raise NotImplementedError(
            'SQS does not support fetching a specific message off the queue.'
        )


