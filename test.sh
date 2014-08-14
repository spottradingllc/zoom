#!/bin/bash
./scripts/bootstrap.sh || exit 1

cd server/ || exit 1

/opt/spot/zoom/venv/bin/nosetests -v ../test/ --with-cov --cover-html --xunit-file=test.xml --with-xunit || exit 1
