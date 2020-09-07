#!/bin/bash
export ALLIGATOR_SLOW=true

echo 'Locmem & SQLite Tests'
export ALLIGATOR_CONN='locmem://'
pytest -s -v --cov=alligator --cov-report=html tests
echo
echo

echo 'Redis Tests'
export ALLIGATOR_CONN='redis://localhost:6379/9'
pytest -s -v tests/test_redis_backend.py
echo
echo

if [[ ! -z "${ALLIGATOR_TESTS_INCLUDE_SQS}" ]]; then
    echo 'SQS Tests'
    echo 'Tests will take ~60 seconds before running, due to PurgeQueue operation restrictions...'
    echo 'Please be patient.'
    export ALLIGATOR_CONN='sqs://us-west-2/'
    pytest -s -v tests/test_sqs_backend.py
    echo
    echo
else
    echo 'Skipping SQS...'
fi
