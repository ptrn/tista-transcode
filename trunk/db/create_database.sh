#! /bin/bash

createuser --no-adduser --no-createdb www-data
createdb --encoding utf-8 tista-transcode

createlang plpythonu tista-transcode

psql tista-transcode < tables.sql

sudo mkdir /var/lib/tista-transcode /var/lib/tista-transcode/cache /var/lib/tista-transcode/cache/snapshots
