import redis

import urlparse


class Client(object):
    def __init__(self, conn_string):
        self.conn_string = conn_string
        bits = urlparse.urlparse(self.conn_string)
        self.conn = self.get_connection(
            host=bits.hostname,
            port=bits.port,
            db=bits.path.lstrip('/').split('/')[0]
        )

    def get_connection(self, host, port, db):
        return redis.StrictRedis(
            host=host,
            port=port,
            db=db
        )

    def len(self, queue_name):
        return self.conn.llen(queue_name)

    def drop_all(self, queue_name):
        task_ids = self.conn.lrange(queue_name, 0, -1)

        for task_id in task_ids:
            self.conn.delete(task_id)

        self.conn.delete(queue_name)

    def push(self, queue_name, task_id, data):
        self.conn.lpush(queue_name, task_id)
        self.conn.set(task_id, data)

    def pop(self, queue_name):
        task_id = self.conn.lpop(queue_name)
        data = self.conn.get(task_id)
        self.conn.delete(task_id)
        return data

    def get(self, queue_name, task_id):
        self.conn.lrem(queue_name, 1, task_id)
        data = self.conn.get(task_id)

        if data:
            self.conn.delete(task_id)
            return data


