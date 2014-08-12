#!/bin/bash

PROJECT_PATH="/opt/spot/zoom"

/bin/bash ${PROJECT_PATH}/scripts/bootstrap.sh || exit 1

${PROJECT_PATH}/venv/bin/nosetests -v test/ --with-cov --cover-html --xunit-file=test.xml --with-xunit || exit 1
