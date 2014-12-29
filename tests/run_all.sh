#!/bin/bash
echo 'Locmem Tests'
export ALLIGATOR_CONN='locmem://'
py.test -s -v --cov=alligator --cov-report=html tests
echo
echo

echo 'Redis Tests'
export ALLIGATOR_CONN='redis://localhost:6379/9'
py.test -s -v tests
