#!/bin/bash

/bin/echo 'Running bootstrap';
./scripts/bootstrap.sh > /dev/null 2>&1 || exit 1

cd server/ || exit 1

/bin/echo 'Starting tests';
/opt/spot/zoom/venv/bin/nosetests -v ../test/ --with-cov --cover-html --xunit-file=test.xml --with-xunit || exit 1
