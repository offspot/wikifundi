#!/bin/sh

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
README_FILE=${DATA_DIR}/README
MEDIAWIKI_CONFIG_FILENAME_CUSTOM=./LocalSettings.custom.php

cp README ${README_FILE} 

mediawiki-init.sh

ln -s ${DATA_DIR} data

if [ ${MIRRORING} ]
then
  #use specific config to mirroring
  cp ${MEDIAWIKI_CONFIG_FILENAME_CUSTOM} ${MEDIAWIKI_CONFIG_FILENAME_CUSTOM}.backup
  cp LocalSettings.mirroring.php ${MEDIAWIKI_CONFIG_FILENAME_CUSTOM}
  
  echo "Start services"
  service nginx start
  service php7.0-fpm start
  service memcached start 
  
  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 

  echo "Start mirroring ..."
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json | tee -a ${LOG_DIR}/mirroring.log 
  
  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 
  echo "Delete old revisions ..."
  php maintenance/deleteOldRevisions.php --delete >> ${LOG_DIR}/mw_update.log 
  #echo "Refresh links ..."
  #php maintenance/refreshLinks.php >> ${LOG_DIR}/mw_update.log 

  echo "Stop services"
  service memcached stop
  service php7.0-fpm stop
  service nginx stop
  
  cp ${MEDIAWIKI_CONFIG_FILE_CUSTOM}.backup ${MEDIAWIKI_CONFIG_FILE_CUSTOM}
fi

if [ ${DEBUG}  ]
then
  /bin/bash
else
  start-services.sh
fi

