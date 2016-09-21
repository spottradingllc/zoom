#!/bin/sh
set -x
docker build --rm -t local/zoom -f docker/zoom/Dockerfile .
