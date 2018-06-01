#!/bin/sh
echo "Database : $DATABASE_NAME"
DATABASE_FILE=/var/www/data/${DATABASE_NAME}.sqlite

chown www-data:www-data /var/www/html/images 
chown www-data:www-data /var/www/data

#Fix latence problem
rm -rf /var/www/data/locks

#Init database
if [ -e ${DATABASE_FILE} ]
then 
  echo "Database already initialized" 
else 
  echo "Database not exist -> Initialize database" 
  #Copy the "empty" database
  cp /tmp/my_wiki.sqlite ${DATABASE_FILE}
  #Allow to write on database
  chmod 644 ${DATABASE_FILE} && chown www-data:www-data ${DATABASE_FILE}
  
  #maintenance
  cd maintenance 
  ./update.php --quick
  cd ..
fi

echo "Starting Persoid ..."
cd parsoid
node bin/server.js &
cd .. 

service memcached start 
service apache2 start

#mirroring
wikimedia_sync -dut mirroring.json 

#maintenance
cd maintenance 
./update.php --quick
cd ..

/bin/bash

#echo "Starting Apache 2 ..."
#apache2ctl -D FOREGROUND

# for debug
#if [ -z "$1" ]
#then
#  echo "Starting Apache 2 ..."
#  apache2ctl -D FOREGROUND
#else
#service apache2 start
#exec "$@"
#fi

