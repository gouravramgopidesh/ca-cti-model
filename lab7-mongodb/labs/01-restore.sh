#!/bin/sh
set -eu
# MongoDB official image executes this only for a new data volume.
mongorestore --host 127.0.0.1 --port 27017 --gzip --archive=/seed/lab7.archive.gz --nsFrom="sentinel_atlas.*" --nsTo="lab7-mongodb.*" --stopOnError
