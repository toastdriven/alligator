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


Update References from ``Task.async`` to ``Task.is_async``
==========================================================

In Python 3, ``async`` is a reserved word.

It can be search & replaced with ``is_async``. Look for places where you're
manually constructing ``Task`` objects or using ``gator.options(async=...)``.

The behavior is the same, just a changed name.


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
