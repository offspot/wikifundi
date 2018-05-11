#!/bin/sh
#cd maintenance \ && ./update.php \ && cd ..
#chown www-data:www-data -r /var/www/html/images

#Allow to write on database
chmod 644 /var/www/data/*.sqlite && chown www-data:www-data /var/www/data/*.sqlite
#Fix latence problem
rm -rf /var/www/data/locks

echo "Starting Persoid ..."
nodejs parsoid/bin/server.js &

service memcached start 

echo "Starting Apache 2 ..."
apache2ctl -D FOREGROUND
# for debug
#service apache2 start
#/bin/bash

