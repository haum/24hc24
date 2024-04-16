#!/bin/bash
sudo docker stop postgres_24hc

sudo docker run --rm --name postgres_24hc -d \
-e POSTGRES_USER="haum" \
-e POSTGRES_PASSWORD="Poseidon" \
-e POSTGRES_DB="odyssee" \
--network=24hc24 \
-v /var/www/odysseehaumere.haum.org/24hc24/dbdata:/var/lib/postgresql/data \
-p 5432:5432 \
postgres:latest
