#!/bin/bash
set -eu
cp /shared/keyfile /tmp/mongodb-keyfile
chown mongodb:mongodb /tmp/mongodb-keyfile
chmod 400 /tmp/mongodb-keyfile
exec docker-entrypoint.sh mongod --replSet rs0 --bind_ip_all --keyFile /tmp/mongodb-keyfile --wiredTigerCacheSizeGB 0.25
