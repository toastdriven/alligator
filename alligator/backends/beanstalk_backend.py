import beanstalkc

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Client(object):
    def __init__(self, conn_string):
        """
        A Beanstalk-based ``Client``.

        :param conn_string: The DSN. The host/port are parsed out of it.
            Should be of the format ``beanstalk://host:port/``
        :type conn_string: string
        """
        self.conn_string = conn_string
        bits = urlparse(self.conn_string)
        self.conn = self.get_connection(
            host=bits.hostname,
            port=bits.port
        )

    def get_connection(self, host, port):
        """
        Returns a ``StrictRedis`` connection instance.
        """
        return beanstalkc.Connection(
            host=host,
            port=port
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
        try:
            stats = self.conn.stats_tube(queue_name)
        except beanstalkc.CommandFailed as err:
            if err[1] == 'NOT_FOUND':
                return 0

            raise

        return stats.get('current-jobs-ready', 0)

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string
        """
        # This is very inefficient, but Beanstalk (as of v1.10) doesn't support
        # deleting an entire tube.
        queue_length = self.len(queue_name)
        self._only_watch_from(queue_name)

        for i in xrange(queue_length):
            job = self.conn.reserve(timeout=0)

            if job:
                job.delete()

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
        # Beanstalk doesn't let you specify a task id.
        self.conn.use(queue_name)
        return self.conn.put(data)

    def _only_watch_from(self, queue_name):
        seen = False

        for watched in self.conn.watching():
            if watched == queue_name:
                seen = True
            else:
                self.conn.ignore(watched)

        if not seen:
            self.conn.watch(queue_name)

    def pop(self, queue_name):
        """
        Pops a task off the queue.

        :param queue_name: The name of the queue. Usually handled by the
            ``Gator`` instance.
        :type queue_name: string

        :returns: The data for the task.
        :rtype: string
        """
        self._only_watch_from(queue_name)
        job = self.conn.reserve(timeout=0)
        job.delete()
        return job.body

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
        self._only_watch_from(queue_name)
        job = self.conn.peek(task_id)

        if not job:
            return

        job.delete()
        return job.body
