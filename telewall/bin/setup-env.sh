#!/bin/bash

command -v virtualenv >/dev/null 2>&1 || sudo pip install virtualenv

cd /telewall

test -d py2-env/ || virtualenv -p /usr/bin/python2.7  py2-env/
source py2-env/bin/activate
pip install -r telewall/requirements.txt
