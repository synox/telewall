#!/bin/bash
cd $(dirname "$0")
cd ..

export PYTHONPATH="."

./py2-env/bin/python telewall/application/cleanup.py
