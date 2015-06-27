BetterPonymotes
===============

This is the official BetterPonymotes source repository. All backend code,
utility scripts, and addon code can be found here.


Requirements
============

The backend requires an SQL database. Development is done exclusively with
PostgreSQL and may not work with other databases.

Suggested basic configuration (does not require a "bpm" user on the operating
system):

    CREATE DATABASE bpm;
    CREATE USER bpm;
    GRANT ALL ON DATABASE bpm TO bpm;

For more complex configurations, esp. password/user authentication or network
connections, refer to PostgreSQL documentation, pg_hba.conf, and
[SQLAlchemy documentation](http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls).

To install required Python packages, the recommended setup is to create a
virtualenv:

    pyvenv venv
    source venv/bin/activate
    ./setup.py develop
