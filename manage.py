#! /usr/bin/env python

from __future__ import absolute_import
from flask.ext.script import Manager
from flask.ext.celery import install_commands as install_celery_commands

from inform import app, views

manager = Manager(app)
install_celery_commands(manager)

@manager.command
def get():
    print views.get().data

if __name__ == "__main__":
    manager.run()
