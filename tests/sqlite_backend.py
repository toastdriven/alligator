import sqlite3
import time


class Client(object):
    def __init__(self, conn_string):
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

        return cur

    def len(self, queue_name):
        query = "SELECT COUNT(task_id) FROM `{}`".format(queue_name)
        cur = self._run_query(query, [])
        res = cur.fetchone()
        return res[0]

    def drop_all(self, queue_name):
        query = "DELETE FROM `{}`".format(queue_name)
        self._run_query(query, [])

    def push(self, queue_name, task_id, data):
        now = int(time.time())
        query = (
            "INSERT INTO `{}` (task_id, data, delay_until) VALUES (?, ?, ?)"
        ).format(queue_name)
        self._run_query(query, [task_id, data, now])
        return task_id

    def pop(self, queue_name):
        now = int(time.time())
        query = (
            "SELECT task_id, data "
            "FROM `{}` "
            "WHERE delay_until <= ?"
            "LIMIT 1"
        ).format(queue_name)
        cur = self._run_query(query, [now])
        res = cur.fetchone()

        query = "DELETE FROM `{}` WHERE task_id = ?".format(queue_name)
        self._run_query(query, [res[0]])

        return res[1]

    def get(self, queue_name, task_id):
        query = "SELECT task_id, data FROM `{}` WHERE task_id = ?".format(
            queue_name
        )
        cur = self._run_query(query, [task_id])
        res = cur.fetchone()

        query = "DELETE FROM `{}` WHERE task_id = ?".format(queue_name)
        self._run_query(query, [task_id])

        return res[1]
