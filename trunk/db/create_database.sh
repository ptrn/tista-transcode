#! /bin/bash

createuser --no-adduser --no-createdb www-data
createdb --encoding utf-8 ttc

createlang plpythonu ttc

psql ttc < tables.sql

sudo mkdir /var/lib/ttc /var/lib/ttc/cache /var/lib/ttc/cache/snapshots
