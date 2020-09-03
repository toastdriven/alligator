#!/bin/bash
echo 'Locmem Tests'
export ALLIGATOR_CONN='locmem://'
pytest -s -v --cov=alligator --cov-report=html tests
echo
echo

echo 'Redis Tests'
export ALLIGATOR_CONN='redis://localhost:6379/9'
pytest -s -v tests
echo
echo
