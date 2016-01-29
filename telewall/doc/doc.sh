#/bin/bash
cd $(dirname "$0")

source ../py2-env/bin/activate

export PYTHONPATH=..
pydoc  -w  ../
