import sqlite3
import time


class Client(object):
    def __init__(self, conn_string):
        """
        A SQLite-based ``Client``.

        Args:
            conn_string (str): The DSN. The host/port/db are parsed out of it.
                Should be of the format ``sqlite:///path/to/db/file.db``
        """
        # This is actually the filepath to the DB file.
        self.conn_string = conn_string
        # Kill the 'sqlite://' portion.
        path = self.conn_string.split("://", 1)[1]
        self.conn = sqlite3.connect(path)

    def _run_query(self, query, args):
        cur = self.conn.cursor()

        if not args:
            cur.execute(query)
        else:
            cur.execute(query, args)

        self.conn.commit()
        return cur

    def setup_tables(self, queue_name="all"):
        """
        Allows for manual creation of the needed tables.

        Args:
            queue_name (str): Optional. The name of the queue. Default is
                `all`.
        """
        # For manually creating the tables...
        query = (
            "CREATE TABLE `queue_{}` "
            "(task_id text, data text, delay_until integer)"
        ).format(queue_name)
        self._run_query(query, None)

    def len(self, queue_name):
        """
        Returns the length of the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                `Gator`` instance.

        Returns:
            int: The length of the queue
        """
        query = "SELECT COUNT(task_id) FROM `queue_{}`".format(queue_name)
        cur = self._run_query(query, [])
        res = cur.fetchone()
        return res[0]

    def drop_all(self, queue_name):
        """
        Drops all the task in the queue.

        Args:
            queue_name (str): The name of the queue. Usually handled by the
                ``Gator`` instance.
        """
        query = "DELETE FROM `queue_{}`".format(queue_name)
        self._run_query(query, [])

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
            delay_until = time.time()

        query = (
            "INSERT INTO `queue_{}` "
            "(task_id, data, delay_until) "
            "VALUES (?, ?, ?)"
        ).format(queue_name)
        self._run_query(query, [task_id, data, int(delay_until)])
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
        now = int(time.time())
        query = (
            "SELECT task_id, data, delay_until "
            "FROM `queue_{}` "
            "WHERE delay_until <= ? "
            "LIMIT 1"
        ).format(queue_name)
        cur = self._run_query(query, [now])
        res = cur.fetchone()

        if res:
            query = "DELETE FROM `queue_{}` WHERE task_id = ?".format(
                queue_name
            )
            self._run_query(query, [res[0]])

            return res[1]

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
        # fmt: off
        query = (
            "SELECT task_id, data "
            "FROM `queue_{}` "
            "WHERE task_id = ?"
        ).format(queue_name)
        # fmt: on
        cur = self._run_query(query, [task_id])
        res = cur.fetchone()

        query = "DELETE FROM `queue_{}` WHERE task_id = ?".format(queue_name)
        self._run_query(query, [task_id])

        return res[1]
