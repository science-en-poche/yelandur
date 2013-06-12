Yelandur
========

[![Build Status](https://travis-ci.org/wehlutyk/yelandur.png?branch=master)](https://travis-ci.org/wehlutyk/yelandur)

Yelandur is the backend API server for:

* [Brainydroid](http://www.brainydroid.com/) on one side: a framework for cognitive experiments on Android devices
* [Naja](https://github.com/wehlutyk/naja) on the other side: a web UI to visualize and retrieve the data resulting from experiments

It's written in Python, using the [Flask](http://flask.pocoo.org/) framework and [MongoDB](http://www.mongodb.org/).


5-minute quick-start
--------------------

Yelandur is tested on Python 2.7. Any other version might (and usually does) generate unexpected errors.

You'll need a working instance of MongoDB. On Debian/Ubuntu this is done by executing:

    sudo apt-get install mongodb
    sudo service mongodb start

If you're not already using [`virtualenv`](http://www.virtualenv.org/en/latest/) and [`virtualenvwrapper`](http://www.doughellmann.com/projects/virtualenvwrapper/), start now. On Debian/Ubuntu this is done by executing:

    sudo apt-get install virtualenvwrapper

and restarting your Bash session.

You will also need to install a few additional packages for the commands below to work. Do this by running:

    sudo apt-get install python-pip mercurial

Next, after cloning the code, `cd` into the repositoryt and run:

    mkvirtualenv yelandur            # Creates a new clean virtual environment and activates it
    pip install -r requirements.txt  # Installs all necessary dependencies in the virtualenv
    python manage.py runserver       # Starts the server

The server starts listening on `0.0.0.0:5000` (i.e. all network addresses, port 5000), and behaves according to the API described in `API.md`.


Testing
-------

Run `nosetests` from the root folder to run all the tests.


What's requirements_dev.txt
---------------------------

`requirements_dev.txt` includes all of `requirements.txt` plus some additional dependencies I use to have Vim behave nicely with Python and unittests. Not necessary to run the server, but handy to hack on the code.
