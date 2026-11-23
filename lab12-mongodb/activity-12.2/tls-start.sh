#!/bin/bash
set -euo pipefail
# Bootstrap only via loopback; no unauthenticated network access.
if [ ! -f /data/db/.lab12-initialized ]; then
  mongod --auth --bind_ip 127.0.0.1 --port 27018 --dbpath /data/db --fork --logpath /tmp/lab12-bootstrap.log --wiredTigerCacheSizeGB 0.25
  trap 'mongod --dbpath /data/db --shutdown >/dev/null 2>&1 || true' EXIT
  if ! mongosh --quiet --port 27018 --eval 'const a=db.getSiblingDB("admin"); a.auth("labadmin",process.env.LAB12_ADMIN_PASSWORD); if (!a.runCommand({usersInfo:"labadmin"}).ok) quit(1);'; then
    mongosh --quiet --port 27018 --eval 'db.getSiblingDB("admin").createUser({user:"labadmin",pwd:process.env.LAB12_ADMIN_PASSWORD,roles:["root"]})'
  fi
  mongosh --quiet --port 27018 --eval 'const a=db.getSiblingDB("admin"); a.auth("labadmin",process.env.LAB12_ADMIN_PASSWORD); if (!a.runCommand({usersInfo:"labadmin"}).ok) quit(1);'
  mongod --dbpath /data/db --shutdown
  trap - EXIT
  touch /data/db/.lab12-initialized
fi
# Run as root inside this isolated lab container; no host ports or host mounts for data.
exec mongod --auth --bind_ip_all --dbpath /data/db --wiredTigerCacheSizeGB 0.25 --tlsMode requireTLS --tlsCertificateKeyFile /certs/server.pem --tlsCAFile /certs/ca.crt
