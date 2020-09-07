.. _migration-to-1.0:

======================
Migration to 1.0 Guide
======================

In the process of going from ``0.10.0`` to ``1.0.0``, a couple things changed
that are not backward-compatible. If you were relying on a previous version,
this is what's needed to update:


Switch to Python 3
==================

It's time. Make the jump to Python 3.

If not, the ``0.10.0`` will continue to be available on PyPI.


Dropped Beanstalk Support
=========================

Unfortunately, the `underlying library`_ (``beanstalkc``) never completed the
transition to Python 3.

As a result, for now, Beanstalk support has been removed. Please consider
either switching backends or staying on the `0.10.0` release.

.. _`underlying library`: https://github.com/earl/beanstalkc


Update References from ``Task.async`` to ``Task.is_async``
==========================================================

In Python 3, ``async`` is a reserved word.

It can be search & replaced with ``is_async``. Look for places where you're
manually constructing ``Task`` objects or using ``gator.options(async=...)``.

The behavior is the same, just a changed name.


Redis Backend: Recreate Queues
==============================

This one is a little painful. You'll need to allow your existing queues to
drain of tasks with your *existing* Alligator install, then run the following:

.. code:: python

    # If your Redis instance (or database) are specifically for Alligator...
    >>> gator.backend.conn.flushdb()

    # If you have other co-mingled data in the Redis instance/database, run:
    >>> gator.backend.conn.delete("all")
    # ...and repeat for any other queue names you have.

After this is done, you can upgrade Alligator to `1.0.0` & simply proceed
as normal.

The reason is due to adding support for delayed/scheduled tasks. Within
Redis, the queue keys switched from a plain `list` to a `sorted set`. As a
result, the commands sent to Redis aren't compatible between `0.10.0` &
`1.0.0`.

Backward compatibility will be maintained throughout the `1.X.X` series, so
changes like this shouldn't occur again for a long time.


Custom Backends: Add ``delay_until`` Support
============================================

As part of the the ``1.0.0`` release, support was added for delayed/scheduled
tasks. If your backend can support timestamps, you can add support if it's
desirable.

Changes needed:

* In the ``Client.push``, add the ``, delay_until=None`` argument at the end
  of the signature & set it on the backend.
* In the ``Client.pop``, add filtering to check for timestamps less than the
  current time.
