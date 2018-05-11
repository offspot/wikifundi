#!/bin/sh
nohup nodejs parsoid/bin/server.js & > /dev/null
service memcached start 
apache2ctl -D FOREGROUND
#/bin/bash

