.. _extending:

===================
Extending Alligator
===================

If you've read the :ref:`tutorial`, you've seen some basic usage of Alligator,
which largely comes down to:

* create a ``Gator`` instance, ...
* use either ``gator.task(...)`` or ``gator.options(...)`` to enqueue the
  task, ...
* and then using either ``latergator.py`` or a custom script with a ``Worker``
  to process the queue.

While this is great in the common/simple case, there may be times where you
need more complex things. Alligator was built for extension, so this document
will outline ways you can get more out of it.


Hook Methods
============

In addition to the task function itself, every task supports three optional
hook functions:

``on_start(task)``
    A function called when the task is first pulled off the queue but
    processing hasn't started.

``on_success(task, result)``
    A function called when the task completes successfully (no exceptions
    thrown). If the task function returns a value, it is passed to this
    function as well.

``on_error(task, err)``
    A function called when the task fails during processing (an exception was
    raised). The exception is passed as well as the failed task.

All together, this lets you do more complex things without muddying the task
function itself. For instance, the following code would log the start/completion
of a task, increment a success count & potentially extend the number of retries
on error.

.. code:: python

    import logging

    from alligator import Gator
    import requests

    from myapp.exceptions import FeedUnavailable, FeedNotFound
    from myapp.utils import cache


    log = logging.getLogger(__file__)


    # This is the main task function.
    def fetch_feeds(feeds):
        for feed_url in feeds:
            resp = requests.get(feed_url)

            if resp.status_code == 503:
                raise FeedUnavailable(feed_url)
            elif resp.status_code != 200:
                raise FeedNotFound(feed_url)

            # Some other processing of the feed data

        return len(feeds)


    # Hook functions
    def log_start(task):
        log.info('Starting to import feeds via task {}...'.format(task.task_id))

    def log_success(task, result):
        log.info('Finished importing {} feeds via task {}.'.format(
            result,
            task.task_id
        ))
        cache.incr('feeds_imported', incr_by=result)

    def maybe_retry_error(task, err):
        if isinstance(err, FeedUnavailable):
            # Try again soon.
            task.retries += 1
        else:
            log.error('Importing feed url {} failed.'.format(str(err)))


    # Now we can use those hooks.
    with gator.options(on_start=log_start, on_success=log_success, on_error=maybe_retry_error) as opts:
        opts.task(fetch_feeds, [
            'http://daringfireball.net/feeds/main',
            'http://xkcd.com/rss.xml',
            'http://www.reddit.com/r/DotA2/.rss',
        ])


Custom Task Classes
===================

Sometimes, just the built-in arguments for ``Task`` (like ``retries``,
``is_async``, ``on_start``/``on_success``/``on_error``) may not be enough. Or
perhaps your hook methods will *always* be the same & you don't want to have to
pass them all the time. Or perhaps you never need the hook methods, but are
running into payload size restrictions by your preferred backend & need some
extra space.

For this, you can create custom ``Task`` classes for use in place of the
built-in one. Since that last restriction can be especially pertinent, let's
show how we'd handle getting more space in our payload.

First, we need a ``Task`` subclass. You can create your own (as long as they
follow the protocol), but subclassing is easier here.

.. code:: python

    # myapp/skinnytask.py
    import bz2

    from alligator import Task


    class SkinnyTask(Task):
        # We're both going to ignore some keys (is_async, options) we don't
        # care about, as well as compress/decompress the payload.
        def serialize(self):
            data = {
                'task_id': self.task_id,
                'retries': self.retries,
                'module': determine_module(self.func),
                'callable': determine_name(self.func),
                'args': self.func_args,
                'kwargs': self.func_kwargs,
            }
            raw_json = json.dumps(data)
            return bz2.compress(raw_json)

        @classmethod
        def deserialize(cls, data):
            raw_json = bz2.decompress(data)
            data = json.loads(data)

            task = cls(
                task_id=data['task_id'],
                retries=data['retries'],
                is_async=data['is_async']
            )

            func = import_attr(data['module'], data['callable'])
            task.to_call(func, *data.get('args', []), **data.get('kwargs', {}))
            return task

Now that we have our ``SkinnyTask``, all we need is to use it. Each ``Gator``
instance supports a ``task_class=...`` keyword argument to replace the class
used. So we'd do:

.. code:: python

    from alligator import Gator

    from myapp.skinnytask import SkinnyTask


    gator = Gator('redis://localhost:6379/0', task_class=SkinnyTask)

Every call to ``gator.task(...)`` or ``gator.options(...)`` will now use our
``SkinnyTask``.

The last bit is that you can no longer use the included ``latergator.py`` script
to process your queue. Instead, you'll have to manually run a ``Worker``.

.. code:: python

    # myapp/skinnylatergator.py
    from alligator import Gator, Worker

    from myapp.skinnytask import SkinnyTask


    gator = Gator('redis://localhost:6379/0', task_class=SkinnyTask)
    # Now the worker will pick up the class as well.
    worker = Worker(gator)
    worker.run_forever()


Multiple Queues
===============

If you have a high-volume site or the priority of tasks is important, the one
main default queue (``alligator.constants.ALL``) may not work well.
Fortunately, each ``Gator`` instance supports customizing the queue name it
places tasks in.

Let's say that sending a notification email is way more important to use than
creating thumbnails of photo uploads. We'll create two ``Gator`` instances, one
for each type of processing.

.. code:: python

    from alligator import Gator

    redis_dsn = 'redis://localhost:'
    email_gator = Gator(redis_dsn, queue_name='notifications')
    image_gator = Gator(redis_dsn, queue_name='images')


    # Later...
    email_gator.task(send_welcome_email, request.user.pk)
    # And elsewhere...
    image_gator.task(create_thumbnail, photo_path)

Now several large uploads won't block the sending of emails later in the queue.
You will however now need to run more ``Workers``. Just like the "Custom Task
Classes" section, your ``Worker`` instances will need either ``email_gator`` or
``image_gator`` passed to them.

You could also fire up many ``email_gator`` workers (say 4) and just 1-2
``image_gator`` workers if the number of tasks justifies it.


Custom Backend Clients
======================

As of the time of writing, Alligator supports the following clients:

* Locmem
* Redis
* Beanstalk

However, if you have a different datastore or queue you'd like to use, you can
write a custom backend ``Client`` to talk to that store. For example, let's
write a naive version based on SQLite using the ``sqlite3`` module included
with Python.

.. warning::

    This code is simplistic for purposes of illustration. It's not thread-safe
    nor particularly suited to large loads. It's a demonstration of how you
    might approach things. Your Mileage May Vary.™

First, we need to create our custom ``Client``. Where you put it doesn't matter
much, as long as it is importable.

Each ``Client`` must have the following methods:

* ``len``
* ``drop_all``
* ``push``
* ``pop``
* ``get``

.. code:: python

    # myapp/sqlite_backend.py
    import sqlite3


    class Client(object):
        def __init__(self, conn_string):
            # This is actually the filepath to the DB file.
            self.conn_string = conn_string
            # Kill the 'sqlite://' portion.
            path = self.conn_string.split('://', 1)[1]
            self.conn = sqlite3.connect(path)

        def _run_query(self, query, args):
            cur = self.conn.cursor()

            if not args:
                cur.execute(query)
            else:
                cur.execute(query, args)

            return cur

        def len(self, queue_name):
            query = 'SELECT COUNT(task_id) FROM `{}`'.format(queue_name)
            cur = self._run_query(query, [])
            res = cur.fetchone()
            return res[0]

        def drop_all(self, queue_name):
            query = 'DELETE FROM `{}`'.format(queue_name)
            self._run_query(query, [])

        def push(self, queue_name, task_id, data):
            query = 'INSERT INTO `{}` (task_id, data) VALUES (?, ?)'.format(
                queue_name
            )
            self._run_query(query, [task_id, data])
            return task_id

        def pop(self, queue_name):
            query = 'SELECT task_id, data FROM `{}` LIMIT 1'.format(queue_name)
            cur = self._run_query(query, [])
            res = cur.fetchone()

            query = 'DELETE FROM `{}` WHERE task_id = ?'.format(queue_name)
            self._run_query(query, [res[0]])

            return res[1]

        def get(self, queue_name, task_id):
            query = 'SELECT task_id, data FROM `{}` WHERE task_id = ?'.format(
                queue_name
            )
            cur = self._run_query(query, [task_id])
            res = cur.fetchone()

            query = 'DELETE FROM `{}` WHERE task_id = ?'.format(queue_name)
            self._run_query(query, [task_id])

            return res[1]

Now using it is simple. We'll make a ``Gator`` instance, passing our new class
via the ``backend_class=...`` keyword argument.

.. code:: python

    from alligator import Gator

    from myapp.sqlite_backend import Client as SQLiteClient


    gator = Gator('sqlite:///tmp/myapp_queue.db', backend_class=SQLiteClient)

And use that ``Gator`` instance as normal!


Different Workers
=================

The ``Worker`` class that ships with Alligator is somewhat opinionated &
simple-minded. It assumes it will be used from a command-line & can print
informational messages to ``STDOUT``.

However, this may not work for your purposes. To work around this, you can
subclass ``Worker`` (or make your own entirely new one).

For instance, let's make ``Worker`` use ``logging`` instead of ``STDOUT``.
We'll swap out all the methods that ``print(...)`` for methods that log instead.

.. code:: python

    # myapp/logworkers.py
    import logging

    from alligator import Worker


    log = logging.getLogger('alligator.worker')


    class LoggingWorker(Worker):
        def starting(self):
            ident = self.ident()
            log.info('{} starting & consuming "{}".'.format(ident, self.to_consume))

            if self.max_tasks:
                log.info('{} will die after {} tasks.'.format(ident, self.max_tasks))
            else:
                log.info('{} will never die.'.format(ident))

        def stopping(self):
            ident = self.ident()
            log.info('{} for "{}" shutting down. Consumed {} tasks.'.format(
                ident,
                self.to_consume,
                self.tasks_complete
            ))

        def result(self, result):
            # Because we don't usually care about the return values.
            log.debug(result)

As with previous ``Worker`` customizations, you won't be able to use
``latergator.py`` anymore. Instead, we'll make a script.

.. code:: python

    # myapp/logginggator.py
    from alligator import Gator

    from myapp.logworkers import LoggingWorker


    gator = Gator('redis://localhost:6379/0')
    worker = LoggingWorker(gator)
    worker.run_forever()

And now there's no more nasty ``STDOUT`` messages!
