#!/bin/bash
echo 'Locmem Tests'
export ALLIGATOR_CONN='locmem://'
py.test -s -v --cov=alligator --cov-report=html tests
echo
echo

echo 'Redis Tests'
export ALLIGATOR_CONN='redis://localhost:6379/9'
py.test -s -v tests
echo
echo

PY_VER=`python --version 2>&1 | cut -c 8`
if [ "$PY_VER" = "2" ]; then
    echo 'Beanstalk Tests'
    export ALLIGATOR_CONN='beanstalk://localhost:11300/'
    py.test -s -v tests
else
    echo "Skipping Beanstalk tests due to Python 3..."
fi
