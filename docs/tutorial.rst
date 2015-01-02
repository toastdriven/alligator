.. _tutorial:

==================
Alligator Tutorial
==================

Alligator is a simple offline task queuing system. It enables you to take
expensive operations & move them offline, either to a different process or
even a whole different server.

This is extremely useful in the world of web development, where request-response
cycles should be kept as quick as possible. Scheduling tasks helps remove
expensive operations & keeps end-users happy.

Some example good use-cases for offline tasks include:

* Sending emails
* Resizing images/creating thumbnails
* Notifying social networks
* Fetching data from other data sources

You should check out the instructions on :ref:`installing` to install Alligator.

Alligator is written in pure Python & can work with all frameworks. For this
tutorial, we'll assume integration with a `Django`_-based web application, but
it could just as easily be used with `Flask`_, `Pyramid`_, pure WSGI
applications, etc.

.. _`Django`: http://djangoproject.com/
.. _`Flask`: http://flask.pocoo.org/
.. _`Pyramid`: http://www.pylonsproject.org/


Philosophy
==========

Alligator is a bit different in approach from other offline task systems. Let's
highlight some ways & the why's.

**Tasks Are Any Plain Old Function**
    No decorators, no special logic/behavior needed inside, no inheritance.
    **ANY** importable Python function can become a task with no modifications
    required.

    Importantly, it must be importable. So instance methods on a class aren't
    processable.

**Plain Old Python**
    Nothing specific to any framework or architecture here. Plug it in to
    whatever code you want.

**Simplicity**
    The code for Alligator should be small & fast. No complex gymnastics, no
    premature optimizations or specialized code to suit a specific backend.

**You're In Control**
    Your code calls the tasks & can setup all the execution options needed.
    There are hook functions for special processing, or you can use your
    own ``Task`` or ``Client`` classes.

    Additionally, you control the consuming of the queue, so it can be
    processed your way (or fanned out, or prioritized, or whatever).


Figure Out What To Offline
==========================

The very first thing to do is figure out where the pain points in your
application are. Doing this analysis differs wildly (though things like
`django-debug-toolbar`_, `profile`_ or `snakeviz`_ can be helpful). Broadly
speaking, you should look for things that:

* access the network
* do an expensive operation
* may fail & require retrying
* things that aren't immediately required for success

If you have a web application, just navigating around & timing pageloads can
be a cheap/easy way of finding pain points.

For the purposes of this tutorial, we'll assume a user of our hot new
Web 3.0 social network made a new post & all their followers need to see it.

So our existing view code might look like:

.. code:: python

    from django.conf import settings
    from django.http import Http404
    from django.shortcuts import redirect, send_email

    from sosocial.models import Post


    def new_post(request):
        if not request.method == 'POST':
            raise Http404('Gotta use POST.')

        # Don't write code like this. Sanitize your data, kids.
        post = Post.objects.create(
            message=request.POST['message']
        )

        # Ugh. We're sending an email to everyone who follows the user, which
        # could mean hundreds or thousands of emails. This could timeout!
        subject = "A new post by {}".format(request.user.username)
        to_emails = [follow.email for follow in request.user.followers.all()]
        send_email(
            subject,
            post.message,
            settings.SERVER_EMAIL,
            recipient_list=to_emails
        )

        # Redirect like a good webapp should.
        return redirect('activity_feed')

.. _`django-debug-toolbar`: https://django-debug-toolbar.readthedocs.org/
.. _`profile`: https://docs.python.org/3.3/library/profile.html
.. _`snakeviz`: https://jiffyclub.github.io/snakeviz/


Creating a Task
===============

The next step won't involve Alligator at all. We'll extract that slow code into
an importable function, then call it from where the code used to be.
So we can convert our existing code into:

.. code:: python

    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import Http404
    from django.shortcuts import redirect, send_email

    from sosocial.models import Post


    def send_post_email(user_id, post_id):
        post = Post.objects.get(pk=post_id)
        user = User.objects.get(pk=user_id)

        subject = "A new post by {}".format(user.username)
        to_emails = [follow.email for follow in user.followers.all()]
        send_email(
            subject,
            post.message,
            settings.SERVER_EMAIL,
            recipient_list=to_emails
        )


    def new_post(request):
        if not request.method == 'POST':
            raise Http404('Gotta use POST.')

        # Don't write code like this. Sanitize your data, kids.
        post = Post.objects.create(
            message=request.POST['message']
        )

        # The code was here. Now we'll call the function, just to make sure
        # things still work.
        send_post_email(request.user.pk, post.pk)

        # Redirect like a good webapp should.
        return redirect('activity_feed')

Now go run your tests or hand-test things to ensure they still work. This is
important because it helps guard against regressions in your code.

You'll note we're not directly passing the ``User`` or ``Post`` instances,
instead passing the primary identifiers, even as it stands it's causing two
extra queries. While this is sub-optimal as things stands, it neatly prepares
us for offlining the task.

.. note::

    **Why not pass the instances themselves?**

    While it's possible to create instances that nicely serialize, the problem
    with this approach is stale data & unnecessarily large payloads.

    While the ideal situation is tasks that are processed within seconds of
    being added to the queue, in the real world, queues can get backed up &
    users may further change data. By fetching the data fresh when processing
    the task, you ensure you're not working with old data.

    Further, most queues are optimized for small payloads. The more data to
    send over the wire, the slower things go. Given that's the opposite reason
    for adding a task queue, it doesn't make sense.


Create a Gator Instance
=======================

While it's great we got better encapsulation by pulling out the logic into
its own function, we're still doing the sending of email in-process, which means
our view is still slow.

This is where Alligator comes in. We'll start off by importing the ``Gator``
class at the top of the file & making an instance.

.. note::

    Unless you're only using Alligator in **one** file, a best practice would
    be to put that import & initialization into it's own file, then import that
    configured ``gator`` object into your other files. Configuring it in one
    place is better than many instantiations (but also allows for setting
    up a different instance elsewhere).

When creating a ``Gator`` instance, you'll need to choose a queue backend.
Alligator ships with support for local-memory, Redis & Beanstalk. See the
:ref:`installing` docs for setup info.

Local Memory
------------

Primarily only for development or in testing, this has no dependencies, but
keeps everything in-process.

.. code:: python

    from alligator import Gator

    # Connect to a locally-running Redis server & use DB 0.
    gator = Gator('redis://localhost:6379/0')


Redis
-----

Redis is a good option for production and small-large installations.

.. code:: python

    from alligator import Gator

    # Connect to a locally-running Redis server & use DB 0.
    gator = Gator('redis://localhost:6379/0')


Beanstalk
---------

Beanstalk specializes in queuing & can be used in production at large-very large
installations.

.. code:: python

    from alligator import Gator

    # Connect to a locally-running Beanstalk server.
    gator = Gator('beanstalk://localhost:11300/')


**For the duration of the tutorial, we'll assume you chose Redis.**


Put the Task on the Queue
=========================

After we make a ``Gator`` instance, the only other change is to how we call
``send_post_email``. Instead of calling it directly, we'll need to enqueue
a task.

There are two common ways of creating a task in Alligator:

``gator.task()``
    A typical function call. You pass in the callable & the
    ``*args``/``**kwargs`` to provide to the callable. It gets put on the
    queue with the default task execution options.

``gator.options()``
    Creates a context manager that has a ``.task()`` method that works
    like the above. This is useful for controlling the task execution options,
    such as retries or if the task should be asynchronous. See the "Working
    Around Failsome Tasks" section below.

Since we're just starting out with Alligator & looking to replicate the
existing behavior, we'll use ``gator.task(...)`` to create & enqueue the task.

.. code:: python

    # Old code
    send_post_email(request.user.pk, post.pk)

    # New code
    gator.task(send_post_email, request.user.pk, post.pk)

Hardly changed in code, but a world of difference in execution speed. Rather
than blasting out hundreds of emails & possibly timing out, a task is placed on
the queue & execution continues quickly. The complete code looks like:

.. code:: python

    from alligator import Gator

    from django.contrib.auth.models import User
    from django.conf import settings
    from django.http import Http404
    from django.shortcuts import redirect, send_email

    from sosocial.models import Post


    # Please configure this once & import it elsewhere.
    # Bonus points if you use a settings (e.g. ``settings.ALLIGATOR_DSN``)
    # instead of a hard-coded string.
    gator = Gator('redis://localhost:6379/0')

    def send_post_email(user_id, post_id):
        post = Post.objects.get(pk=post_id)
        user = User.objects.get(pk=user_id)

        subject = "A new post by {}".format(user.username)
        to_emails = [follow.email for follow in user.followers.all()]
        send_email(
            subject,
            post.message,
            settings.SERVER_EMAIL,
            recipient_list=to_emails
        )


    def new_post(request):
        if not request.method == 'POST':
            raise Http404('Gotta use POST.')

        # Don't write code like this. Sanitize your data, kids.
        post = Post.objects.create(
            message=request.POST['message']
        )

        # The function call was here. Now we'll create a task then carry on.
        gator.task(send_post_email, request.user.pk, post.pk)

        # Redirect like a good webapp should.
        return redirect('activity_feed')


Running a Worker
================

Time to kick back, relax & enjoy your speedy new site, right?

Unfortunately, not quite. Now we're successfully queuing up tasks for later
processing & things are completing quickly, but *nothing is processing those
tasks*. So we need to run a ``Worker`` to consume the queued tasks.

We have two options here. We can either use the included ``latergator.py``
script or we can create our own. The following are identical in function:

.. code:: bash

    $ latergator.py redis://localhost:6379/0

Or...

.. code:: python

    # Within something like ``run_tasks.py``...
    from alligator import Gator, Worker

    # Again, bonus points for an import and/or settings usage.
    gator = Gator('redis://localhost:6379/0')

    worker = Worker(gator)
    worker.run_forever()

Both of these will create a long-running process, which will consume tasks off
the queue as fast as they can.

While this is fine to start off, if you have a heavily trafficked site, you'll
likely need many workers. Simply start more processes (using a tool like
`Supervisor`_ works best).

You can also make things like management commands, build other custom tooling
around processing or even launch workers on their own dedicated servers.

.. _`Supervisor`: http://supervisord.org/


Working Around Failsome Tasks
=============================

Sometimes tasks don't always succeed on the first try. Maybe the database is
down, the mail server isn't working or a remote resource can't be loaded. As it
stands, our task will try once then fail loudly.

Alligator also supports retrying tasks, as well as having an ``on_error`` hook.
To specify we want retries, we'll have to use the other important bit of
Alligator, ``Gator.options``.

``Gator.options`` gives you a context manager & allows you to configure task
execution options that then apply to all tasks within the manager. Using that
looks like:

.. code:: python

    # Old code
    # gator.task(send_post_email, request.user.pk, post.pk)

    # New code
    with gator.options(retries=3) as opts:
        # Be careful to use ``opts.task``, not ``gator.task`` here!
        opts.task(send_post_email, request.user.pk, post.pk)

Now that task will get three retries when it's processed, making network
failures much more tolerable.


Testing Tasks
=============

All of this is great, but if you can't test the task, you might as well not
have code.

Alligator supports an ``async=False`` option, which means that
rather than being put on the queue, your task runs right away (acting like you
just called the function, but with all the retries & hooks included).

.. code:: python

    # Bonus points for using ``settings.DEBUG`` (or similar) instead of a
    # hard-coded ``False``.
    with gator.options(async=False) as opts:
        opts.task(send_post_email, request.user.pk, post.pk)

Now your existing integration tests (from before converting to offline tasks)
should work as expected.

.. warning::

    Make sure you don't accidently commit this & deploy to production. If
    so, why have an offline task system at all?

Additionally, you get naturally improved ability to test, because now your
tasks are just plain old functions. This means you can typically just import
the function & write tests against it (rather than the whole view), which
makes for better unit tests & fewer integration tests to ensure things work
right.


Going Beyond
============

This is 90%+ of the day-to-day usage of Alligator, but there's plenty more
you can do with it.

You may wish to peruse the :ref:`bestpractices` docs for ideas on how to keep
your Alligator clean & flexible.

If you need more custom functionality, the :ref:`extending` docs have
examples on:

* Customizing task behavior using the ``on_start/on_success/on_error`` hook
  functions.
* Custom ``Task`` classes.
* Multiple queues & ``Workers`` for scalability.
* Custom backends.
* ``Worker`` subclasses.

Happy queuing!
