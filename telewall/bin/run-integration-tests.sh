#!/bin/bash
cd $(dirname "$0")
cd ..

source py2-env/bin/activate
export PYTHONPATH="."
nosetests --verbosity=2 --with-xunit telewall/integrationtests
