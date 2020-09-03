.. _bestpractices:

==============
Best Practices
==============

Moving to offlining tasks requires some shifts in the way you develop your
code. There are also some good tricks/ideas for integrating Alligator.

If you have suggestions for other best practices, please submit a pull request
at https://github.com/toastdriven/alligator/pulls!


Configure One ``Gator``
=======================

This is alluded to in the :ref:`tutorial`, but unless you have advanced needs,
you're probably best off configuring a **single** ``Gator`` instance in your
code. Then you can import that instance wherever you need it.

Generally speaking, you'll want to create a new file for just this, though if
you have a ``utils.py`` or other common file, you can add it there. For
example:

.. code:: python

    # Create a new file, like ``myapp/gator.py``
    from alligator import Gator

    gator = Gator('redis://localhost:6379/0')

Then your code elsewhere imports it:

.. code:: python

    # ``myapp/views.py``
    from myapp.gator import gator

    # ...Later...
    def previously_slow_view(request):
        gator.task(expensive_cache_rebuild, user_id=request.user.pk)

This helps :abbr:`DRY (Don't Repeat Yourself)` up your code. It also helps you
avoid having to change many files if you change backends or configuration.


Use Environment Variables or Settings for the ``Gator`` DSN
===========================================================

Instead of hard-coding the :abbr:`DSN (Data Source Name)` for each ``Gator``
instance, you should rely on a configuration setting instead.

If you're using plain old Python or subscribe to the `Twelve-Factor App`_,
you might lean on environment variables set in the shell. For instance, the
Alligator test suite does:

.. code:: python

    import os

    from alligator import Gator


    # Lean on the ENV variable.
    gator = Gator(os.environ['ALLIGATOR_CONN'])

Then when running your app, you could do the following in development, for
ease of setup:

.. code:: bash

    $ export ALLIGATOR_CONN=locmem://
    $ python myapp.py

But the following on production, for handling large loads:

.. code:: bash

    $ export ALLIGATOR_CONN=redis://some.dns.name.com:6379/0
    $ python myapp.py

If you're using something like `Django`_, you could lean on ``settings``
instead, like:

.. code:: python

    from alligator import Gator

    from django.conf import settings


    # Lean on the settings variable.
    gator = Gator(settings.ALLIGATOR_CONN)

And have differing settings files for development vs. production.

.. _`Twelve-Factor App`: http://12factor.net/
.. _`Django`: http://djangoproject.com/


Use an Alternate Queue for Testing
==================================

This is an **important** one. By default, Alligator doesn't make any assumptions
about what environment (development, testing, production) it is in. So the same
queue name will be used.

Especially if you have a shared queue setup for running tests, you can
**accidentally** add testing data to your queue! There are two possible
resolutions to this:

1. Don't Share

    Set your testing environment up such that it has it's own queue stack. This
    will nicely isolate things & not require any code changes.

2. Prefix your ``queue_name``

    If you must share setup (for instance, developing & testing on the same
    machine), use a similar approach to the "Env/Settings for Gator DSN" tip,
    providing a prefix for your queue name. For example::

.. code:: python

    import os

    from alligator import Gator


    # Lean on the ENV variable for a queue prefix.
    gator = Gator(
        'redis://localhost:6379/0',
        # If you ``export ALLIGATOR_PREFIX=test```, your queue name
        # becomes 'test_all'. If not set, it's just 'all'.
        queue_name='_'.join([os.environ.get('ALLIGATOR_PREFIX', ''), 'all'])
    )


Use Environment Variables or Settings for ``Task.is_async``
===========================================================

If you're just using ``gator.task`` & trying to write tests, you may have a
hard time verifying behavior in an integration test (though you should be able
to just unit test the task function).

On the other hand, if you use the ``gator.options`` context manager & supply
an ``is_async=False`` execution option, integration tests become easy, as the
expense of possibly accidentally committing that & causing issues in production.

The best approach is to use the ``gator.options`` context manager, but use
an environment variable/setting to control if things run asynchronously.

.. code:: python

    import os

    # Using the above tip of a single import...
    from myapp.gator import gator


    def some_view(request):
        with gator.options(is_async=os.environ['ALLIGATOR_ASYNC']) as opts:
            opts.task(expensive_thing)

This allows you to set ``export ALLIGATOR_ASYNC=False`` in development/testing
(so the task runs right away in-process) but queues appropriately in
production.


Simple Task Parameters
======================

When creating task functions, you want to simplify the arguments passed to it,
as well as removing as many assumptions as possible.

You may be tempted to try to save queries by passing full objects or large lists
of things as a parameter.

However, you must remember that the task may run at a very different time
(perhaps hours in the future if you're overloaded) or on a completely different
machine than the one scheduling the task. Data goes stale easily & few things
are as frustrating to debug as stale data being re-written over the top of new
data.

Where possible, do the following things:

* Pass primary keys or identifiers instead of rich objects
* Persist large collections in the database or elsewhere, then pass a lookup
  identifier to the task
* Use simple data types, as they serialize well & result in smaller queue
  payloads, meaning faster scheduling & consuming of tasks


Re-use the ``Gator.options`` Context Manager
============================================

All the examples in the Alligator docs show creating a single task within
a ``gator.options(...)`` context manager. So you might be tempted to write code
like:

.. code:: python

    with gator.options(retries=3) as opts:
        opts.task(send_mass_mail, list_id)

    with gator.options(retries=3) as opts:
        opts.task(update_follow_counts, request.user.pk)

However, you can reuse that context manager to provide the same execution
options to **all** tasks within the block. So we can clean up & shorten our
code to:

.. code:: python

    with gator.options(retries=3) as opts:
        opts.task(send_mass_mail, list_id)
        opts.task(update_follow_counts, request.user.pk)

Two unique tasks will still be created, but both will have the ``retries=3``
provided to better ensure they succeeed.
