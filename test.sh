#!/bin/bash

VENV_DIR=$PWD/venv
/bin/echo 'Running bootstrap';
./scripts/bootstrap.sh $VENV_DIR > /dev/null 2>&1 || exit 1

cd server/ || exit 1

/bin/echo 'Starting tests';
$VENV_DIR/bin/nosetests -v ../test/ --with-cov --cover-html --xunit-file=test.xml --with-xunit || exit 1
