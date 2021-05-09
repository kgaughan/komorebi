========
komorebi
========

The code under here is meant to allow me to migrate to what I hope is a more
permanent setup for all my online stuff. Fundamentally, the project is to
deprecate stereochro.me as a website.

The project will be a partial port of my old PHP code over to a WSGI app of
some sort written in Python. Additionally, I'll be replacing the database with
SQLite, though I'm slightly worried about data corruption issues there.

The pages functionality is due to be replaced with a set of permanent
redirects to my blog. The linklog is probably going to be moved to
talideon.com/links, with permanent redirects forwarding there for linklog
entries, and posts redirecting to the weblog.

The output cache functionality will be replaced with Redis.

Prep
====

Run::

    make develop

Development server
==================

Run::

    make run

The username and password specified in ``dev/dev.htpasswd`` are *username* and
*password* respectively.

Deployment
==========

The ``komorebi`` module containst a ``__main__.py`` file. This means that the
module is executable. This default runner uses wsgiref_. Use the ``--help``
flag for a list of options. Under the ``supevision`` directory is
``komorebi.ini``, a config file for Supervisor_ showing how to run the site.

.. _wsgiref: https://docs.python.org/3.7/library/wsgiref.html
.. _Supervisor: http://supervisord.org/

TODO
====

* Get `Flask-Caching`__ into the FreeBSD ports tree so I can use it. This is
  needed because the mechanism used to generate the archive page is a bit
  crazy.
* Some kind of simple admin backend to allow editing and posting of new
  entries. Or if I were feeling particularly inspired, I could implement
  Micropub__...
* Remove hardwired stuff, such as the blog name, author, copyright notice,
  feed ID prefix, &c.

.. __: https://github.com/sh4nks/flask-caching
.. __: https://www.w3.org/TR/micropub/

.. vim:set ft=rst:
