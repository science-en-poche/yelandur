# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='Yelandur',
    version='0.1',
    author='Sébastien Lerique',
    author_email='sl@mehho.net',
    packages=['yelandur', 'yelandur.auth', 'yelandur.users',
              'yelandur.devices'],
    license='GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007',
    description='Backend server for experiments on smartphones',
    long_description=open('README.md').read(),
    url='https://github.com/wehlutyk/yelandur'
)
