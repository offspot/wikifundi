#!/bin/sh

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
README_FILE=${DATA_DIR}/README

cp README ${README_FILE} 

mediawiki-init.sh

ln -s ${DATA_DIR} data

if [ ${MIRRORING} ]
then
  service nginx start
  service php7.0-fpm start
  service memcached start 

  echo "Starting mirroring ..."
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json | tee -a ${LOG_DIR}/mirroring.log 

  chown -R www-data:www-data ${DATA_DIR}
  
  echo "Starting Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 
  php maintenance/deleteOldRevisions.php --delete
  php maintenance/refreshLinks.php >> ${LOG_DIR}/mw_update.log 

  service memcached stop
  service php7.0-fpm stop
  service nginx stop
fi

if [ ${DEBUG}  ]
then
  /bin/bash
else
  start-services.sh
fi

