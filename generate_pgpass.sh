#!/bin/bash

export $(cat .env | grep -v '^#' | xargs)

cat > servers.json << SERVERS
{
  "Servers": {
    "1": {
      "Name": "Mandera Postgres",
      "Group": "Servers",
      "Host": "mandera_postgres",
      "Port": 5432,
      "MaintenanceDB": "${POSTGRES_DB}",
      "Username": "${POSTGRES_USER}",
      "SSLMode": "prefer",
      "PassFile": "/pgpass"
    }
  }
}
SERVERS

echo "mandera_postgres:5432:${POSTGRES_DB}:${POSTGRES_USER}:${POSTGRES_PASSWORD}" > pgpass
chmod 600 pgpass

echo "servers.json and pgpass generated from .env"
