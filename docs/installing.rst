.. _installing:

====================
Installing Alligator
====================

Installation of Alligator itself is a relatively simple affair. For the most
recent stable release, simply use pip_ to run::

    $ pip install alligator

Alternately, you can download the latest development source from Github::

    $ git clone https://github.com/toastdriven/alligator.git
    $ cd alligator
    $ python setup.py install

.. _pip: http://pip-installer.org/


Queue Backends
==============

Alligator includes a ``Local Memory Client``, which is useful for development
or testing (no setup required). However, this is not very scalable.

For production use, you should install one of the following servers used for
queuing:


Redis
-----

A in-memory data structure server, it offers excellent speed as well as being
a frequently-already-installed server. Official releases can be found at
http://redis.io/download.

You can also install via other package managers::

    # On Mac with Homebrew
    $ brew install redis

    # On Ubuntu
    $ sudo aptitude install redis


Beanstalk
---------

Support for beanstalk is coming in a future release.
