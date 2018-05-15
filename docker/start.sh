#!/bin/sh

cd maintenance \ && ./update.php --quick \ && cd ..
chown www-data:www-data /var/www/html/images 
chown www-data:www-data /var/www/data

echo "Database : $DATABASE_NAME"
DATABASE_FILE=/var/www/data/${DATABASE_NAME}.sqlite

#Init database
if [ -e ${DATABASE_FILE} ]
then 
  echo "Database already initialized" 
else 
  cp /tmp/my_wiki.sqlite ${DATABASE_FILE}
fi

#Allow to write on database
chmod 644 ${DATABASE_FILE} && chown www-data:www-data ${DATABASE_FILE}

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

