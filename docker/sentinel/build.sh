#!/bin/sh
set -x
docker build --rm -t local/sentinel -f docker/sentinel/Dockerfile .
