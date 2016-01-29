#!/bin/bash
cd $(dirname "$0")
cd ..

 
source py2-env/bin/activate
export PYTHONPATH=".:$PYTHONPATH"

pip install --quiet nosexcover
pip install --quiet pylint

nosetests --with-xcoverage --with-xunit --cover-package=telewall  --cover-inclusive  --cover-branches --cover-xml-file=cover.xml --cover-erase telewall/tests/*.py

pylint -f parseable telewall | tee pylint.out
