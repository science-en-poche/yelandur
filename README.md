Yelandur
========

Build status: [![Build Status](https://travis-ci.org/wehlutyk/yelandur.png?branch=master)](https://travis-ci.org/wehlutyk/yelandur)

Yelandur is the backend API server for:

* [Brainydroid](http://www.brainydroid.com/) on one side: a framework for cognitive experiments on Android devices
* [Naja](https://github.com/wehlutyk/naja) on the other side: a web UI to visualize and retrieve the data resulting from experiments

It's written in Python, using the [Flask](http://flask.pocoo.org/) framework and [MongoDB](http://www.mongodb.org/).


5-minute quick-start
--------------------

You'll need a working instance of MongoDB. On Debian/Ubuntu this is done by:

    sudo apt-get install mongodb
    sudo service mongodb start

If you're not already using [`virtualenv`](http://www.virtualenv.org/en/latest/) and [`virtualenvwrapper`](http://www.doughellmann.com/projects/virtualenvwrapper/), start now. On Debian/Ubuntu this is done by:

    sudo apt-get install python-virtualenv virtualenvwrapper

and restarting your Bash session.

Next, after cloning the code, `cd` into it and run:

    mkvirtualenv yelandur   # Creates a new clean virtual environment and activates it
    pip install -r requirements.txt
    python manage.py runserver

The server starts listening on `0.0.0.0:5000` (i.e. all network addresses, port 5000), and behaves according to the API described in `API.md`.


Testing
-------

Run `nosetests` at the root of the code to run all the tests.
