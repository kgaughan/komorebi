========
komorebi
========

The code under here is meant to allow me to migrate to what I hope is a more
permanent setup for all my online stuff. Fundamentally, the project is to
deprecate stereochro.me as a website.

The project will be a partial port of my old PHP code over to a WSGI app of
some sort written in Python.

The pages functionality is due to be replaced with a set of permanent
redirects to my blog. The linklog is probably going to be moved to
talideon.com/links, with permanent redirects forwarding there for linklog
entries, and posts redirecting to the weblog.

The output cache functionality will be replaced with Redis.

Prep
====

Install just__ as a task runner. Run::

    just devel

.. __: https://github.com/casey/just

Development server
==================

Run::

    just dev-server

The username and password specified in ``dev/dev.passwd.json`` are *username*
and *password* respectively.

If you want to create/update a password file, run::

     uv run komorebi-passwd

Deployment without a container
==============================

The ``komorebi`` module contains a ``__main__.py`` file. This means that the
module is executable. This default runner uses wsgiref_, so it's not really
suitable for production usage, but it's enough for testing things out before
configuring a more suitable WSGI server.

The application expects an environment variable called ``KOMOREBI_SETTINGS``
to contain the *absolute* path of a configuration file. If it's not absolute,
Flask will, for reasons, assume it's relative to the ``komorebi`` module
itself, which you don't want. The configuration is a Python file with the
following format:

.. code-block:: python

    # The feed ID to be used in for your site. I recommend you use a tag URI
    # for # this. Substitute 'example.com' with the domain name of your
    # website, '2005' with the current year, and 'komorebi' with whatever you
    # want so long as it's descriptive and consists of alphanumeric characters.
    # This # will be used to construct the Atom feed ID for your feed and also
    # the entry IDs for each entry by appending ':<id>' to the end of it.
    FEED_ID = "tag:example.com,2005:komorebi"

    # A secret key used for signing things within the application. Generate it
    # by running:
    #    python3 -c 'import secrets; print(secrets.token_hex())'
    SECRET_KEY = "deadbeef"

    # Configuration for your blog's database. Currently only FirebirdSQL is
    # supported.
    DB_HOST = "localhost"
    DB_DATABASE = "komorebi.fdb"
    DB_USER = "komorebi"
    DB_PASSWORD = "DbPass123!"

    # Cache configuration. To disable caching, use `NullCache`. For further
    # details, see https://flask-caching.readthedocs.io/en/latest/
    CACHE_TYPE = "FileSystemCache"
    CACHE_DIR = "/path/to/cache"

    # Path to the password store for your application. You can manage these
    # files by running:
    #     uv run komorebi-password
    PASSWD_PATH = "/path/to/config/passwd.json"

    # The title to use for your blog, along with your name for the feed.
    BLOG_TITLE = "My Weblog"
    BLOG_AUTHOR = "Joe Bloggs"

This can include any of the `Flask configuration values`_ too, if they're
relevant to you.

Under the ``supervision`` directory is ``komorebi.ini``, a config file for
Supervisor_ showing how to run the site.

To run with gunicorn_, run::

    gunicorn 'komorebi:create_wsgi_app()'

This assumes that Komorebi and its dependencies are installed and you have
``KOMOREBI_SETTINGS`` suitably configured in your environment.

.. _wsgiref: https://docs.python.org/3.7/library/wsgiref.html
.. _Supervisor: http://supervisord.org/
.. _Flask configuration values: https://flask.palletsprojects.com/en/stable/config/#builtin-configuration-values
.. _gunicorn: https://gunicorn.org/

Deployment with a container locally
===================================

To build a container image locally with podman_, run::

    just container

This will build an image called ``ghcr.io/kgaughan/komorebi:latest``.

.. _podman: https://podman.io/

Create a configuration file called ``komorebi.cfg`` and a password database
called ``passwd.json`` in a directory as documented above.

You can create a container from it with::

    $ podman container create --init --network=host --name=komorebi \
        --env=KOMOREBI_SETTINGS=/config/komorebi.cfg \
        --mount=type=bind,src=/path/to/config,destination=/config,ro=true \
        --mount=type=tmpfs,destination=/cache \
        ghcr.io/kgaughan/komorebi:latest

(Obviously using ``--network=host`` isn't ideal, but it's fine for trying
things out.)

Here, ``/path/to/config`` the path to a directory outside the container in
which you've previously put the configuration. Now, start it::

    $ podman container start komorebi

Regenerating subresource integrity hashes
=========================================

Run::

    just sri

SRI is less trouble than dealing with CSP. I should add something to generate a
manifest of this stuff to avoid manual updates.

TODO
====

* Some kind of simple admin backend to allow editing and posting of new
  entries. Or if I were feeling particularly inspired, I could implement
  Micropub__...
* Remove hardwired stuff, such as the blog name, author, copyright notice,
  feed ID prefix, &c.

.. __: https://github.com/sh4nks/flask-caching
.. __: https://www.w3.org/TR/micropub/

.. vim:set ft=rst:
