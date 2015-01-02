Alligator
=========

.. image:: https://travis-ci.org/toastdriven/alligator.png?branch=master
        :target: https://travis-ci.org/toastdriven/alligator

Simple offline task queues. For Python.

"See you later, alligator."


Requirements
------------

* Python 2.6+ or Python 3.3+
* (Optional) ``redis`` for the Redis backend
* (Optional) ``beanstalkc`` for the Beanstalk backend
* (Optional) ``PyYAML`` for the Beanstalk backend


WHY?!!1!
--------

* Because I have NIH-syndrome.
* Or because I longed for something simple (~375 loc).
* Or because I wanted something with tests (90%+ coverage) & docs.
* Or because I wanted pluggable backends.
* Or because testing some other queuing system was a pain.
* Or because I'm an idiot.


Basic Usage
-----------

This example uses Django, but there's nothing Django-specific about Alligator.

I repeat, You can use it with **any** Python code that would benefit from
background processing.

.. code:: python

    from alligator import Gator

    from django.contrib.auth.models import User
    from django.shortcuts import send_email


    # Make a Gator instance.
    # Under most circumstances, you would configure this in one place &
    # import that instance instead.
    gator = Gator('redis://localhost:6379/0')


    # The task itself.
    # Nothing special, just a plain *undecorated* function.
    def follow_email(followee_username, follower_username):
        followee = User.objects.get(username=followee_username)
        follower = User.objects.get(username=follower_username)

        subject = 'You got followed!'
        message = 'Hey {}, you just got followed by {}! Whoohoo!'.format(
            followee.username,
            follower.username
        )
        send_email(subject, message, 'server@example.com', [followee.email])


    # An simple, previously expensive view.
    @login_required
    def follow(request, username):
        # You'd import the task function above.
        if request.method == 'POST':
            # Schedule the task.
            # Use args & kwargs as normal.
            gator.task(follow_email, request.user.username, username)
            return redirect('...')


Running Tasks
-------------

Rather than trying to do autodiscovery, fanout, etc., you control how your
workers are configured & what they consumer.

If your needs are simple, run the included ``latergator.py`` worker:

.. code:: bash

    $ python latergator.py redis://localhost:6379/0

If you have more complex needs, you can create a new executable file
(bin script, management command, whatever) & drop in the following code.

.. code:: python

    from alligator import Gator, Worker

    # Bonus points if you import that one pre-configured ``Gator`` instead.
    gator = Gator('redis://localhost:6379/0')

    # Consume & handle all tasks.
    worker = Worker(gator)
    worker.run_forever()


License
-------

New BSD


Complex Usage (For Future Docs)
-------------------------------

.. code:: python

    # We're re-using the above imports/setup.

    def log_func(job):
        # A simple example of logging a failed task.
        if job.result != SUCCESS:
            logging.error("Job {} failed.".format(job.id))

    # A context manager for supplying options
    with gator.options(retries=3, async=settings.ASYNC_TASKS, on_error=log_func) as task:
        feeds_job = task(sketchy_fetch_feeds, timeout=30)


    # Future wishlist items...

    # Dependent tasks, will only run if the listed tasks succeed.
    with gator.options(depends_on=[feeds_job]) as task:
        task(rebuild_cache)

    # Delayed tasks (run in an hour).
    with gator.options(run_after=60 * 60) as task:
        task(this_can_wait)


Running Tests
-------------

Alligator has 95%+ test coverage & aims to be passing/stable at all times.

If you'd like to run the tests, clone the repo, then run::

    $ virtualenv env2
    $ . env2/bin/activate
    $ pip install -r requirements.txt
    $ python setup.py develop
    $ py.test -s -v --cov=alligator --cov-report=html tests


TODO
----

* Scheduled tasks
* Dependent tasks
* Cancellable tasks
