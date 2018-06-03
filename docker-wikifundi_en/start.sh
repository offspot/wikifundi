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
  
  # if new databse, always mirroring
  MIRRORING=1
fi

echo "Starting Persoid ..."
cd parsoid
node bin/server.js > /dev/null &
cd .. 

service memcached start 

if [ ${MIRRORING} ]
then
  #mirroring
  #service apache2 start
  echo "Start Mirroring, log in data/mirroring.log"
  wikimedia_sync ${MIRRORING_OPTIONS} mirroring.json > /var/www/data/mirroring.log &
  #service apache2 stop
  #maintenance
  #cd maintenance 
  #./update.php --quick
  #cd ..
fi

#finnaly, start apache and wait
echo "Starting Apache 2 ..."
apache2ctl -D FOREGROUND

# for debug
#/bin/bash
#if [ -z "$1" ]
#then
#  echo "Starting Apache 2 ..."
#  apache2ctl -D FOREGROUND
#else
#service apache2 start
#exec "$@"
#fi

