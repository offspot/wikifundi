#!/bin/sh
echo "Database : $DATABASE_NAME"
DATABASE_FILE=/var/www/data/${DATABASE_NAME}.sqlite

DATA_DIR=/var/www/data
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
LOG_DIR=${DATA_DIR}/log
CFG_DIR=${DATA_DIR}/config

mkdir -p ${DATA_DIR}/images ${LOG_DIR} ${CFG_DIR}
chown www-data:www-data ${DATA_DIR}
chown www-data:www-data ${DATA_DIR}/images 
chown www-data:www-data ${LOG_DIR} ${CFG_DIR}

#if LocalSettings.custom.php is not a sym link,
# then move this file and create the link
if [ -f ./LocalSettings.custom.php ]
then
  mv ./LocalSettings.custom.php ${CFG_DIR}/LocalSettings.${DATABASE_NAME}.php
  ln -s ${CFG_DIR}/LocalSettings.${DATABASE_NAME}.php ./LocalSettings.custom.php
fi

#Fix latence problem
rm -rf ${DATA_DIR}/locks

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
  
  #change Admin password
  php maintenance/createAndPromote.php --bureaucrat --sysop --bot --force Admin ${MEDIAWIKI_ADMIN_PASSWORD}  
  
  #maintenance
  echo "Start MediaWiki Maintenance"
  cd maintenance 
  ./update.php --quick > ${LOG_DIR}/mw_update.log 
  cd ..
  
  # if new databse, always mirroring
  MIRRORING=1
fi

echo "Starting Persoid ..."
cd parsoid
node bin/server.js > ${LOG_DIR}/parsoid.log  &
cd .. 

service memcached start 

if [ ${MIRRORING} ]
then
  #mirroring
  service apache2 start
  echo "Start Mirroring, log in data/mirroring.log"
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json > ${LOG_DIR}/mirroring.log 
  service apache2 stop
  
  #maintenance
  echo "Start MediaWiki Maintenance"
  cd maintenance 
  ./update.php --quick > ${LOG_DIR}/mw_update.log 
  php refreshLinks.php > ${LOG_DIR}/mw_update.log 
  cd ..  
  
  #build tarbal
  cd ${DATA_DIR}
  #compress database 
  gzip -c ${DATABASE_NAME}.sqlite > ${DATABASE_NAME}.sqlite.gz
  #create tarbal
  tar -cvvf data-${DATABASE_NAME}.tar ${DATABASE_NAME}.sqlite.gz log config images >> ${LOG_DIR}/mirroring.log 
  rm -f ${DATABASE_NAME}.sqlite.gz
  cd ../html
  ln -s ${DATA_DIR}/data-${DATABASE_NAME}.tar
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

