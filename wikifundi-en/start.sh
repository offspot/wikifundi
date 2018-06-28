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
  cp -f ./LocalSettings.custom.origin.php ${CFG_DIR}/LocalSettings.custom.php
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
else
  # ignore mirroring LocalSettings
  echo '<?php ?>' > ./LocalSettings.mirroring.php
fi

if [ ! ${DEBUG}  ]
then
  # ignore debug LocalSettings
  echo '<?php ?>' > ./LocalSettings.debug.php
fi

if [ ${GO_BASH}  ]
then
  /bin/bash
else
  start-services.sh
fi
