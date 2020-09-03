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

if [[ ! -z "${ALLIGATOR_TESTS_INCLUDE_SQS}" ]]; then
    echo 'SQS Tests'
    export ALLIGATOR_CONN='sqs://us-west-2/'
    pytest -s -v tests
    echo
    echo
else
    echo 'Skipping SQS...'
fi
