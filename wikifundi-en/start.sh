#!/bin/bash

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
README_FILE=${DATA_DIR}/README
CFG_DIR=${DATA_DIR}/config

function clean {
  echo "Delete old revisions ..."
  php maintenance/deleteOldRevisions.php --delete  
  echo "Delete archive file ..." 
  php maintenance/deleteArchivedFiles.php --delete  
  echo "Delete thumb, temp and archive ..."
  rm -rvf ${DATA_DIR}/images/thumb/* ${DATA_DIR}/images/temp/* ${DATA_DIR}/images/archive/*
}

cp README ${README_FILE} 

mediawiki-init.sh

ln -s ${DATA_DIR} data

if [ ${CLEAN} ]
then
  clean
fi

if [ ${MIRRORING} ]
then
  #use specific config to mirroring
  ln -fs ./LocalSettings.mirroring.php ./LocalSettings.custom.php

  echo "Start services ..."
  start-services.sh  

  #Allow to write on database
  chmod 644 ${DATABASE_FILE}  
  
  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 

  echo "Start mirroring ..."
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json | tee -a ${LOG_DIR}/mirroring.log 

  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 
  clean
  #echo "Refresh links ..."
  #php maintenance/refreshLinks.php >> ${LOG_DIR}/mw_update.log 
  #To write in image dir
  chown -R www-data:www-data ${DATA_DIR}

  #use config in volume 
  ln -fs ${CFG_DIR}/LocalSettings.custom.php ./LocalSettings.custom.php
fi

if [ ${DEBUG}  ]
then
  ln -fs ./LocalSettings.debug.php ./LocalSettings.custom.php
fi

start-services.sh

if [ ${BASH}  ]
then
  /bin/bash
fi
