#!/bin/bash

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
README_FILE=${DATA_DIR}/README
CFG_DIR=${DATA_DIR}/config

cp README ${README_FILE} 

mediawiki-init.sh

ln -s ${DATA_DIR} data

if [ ${MIRRORING} ]
then

  #Allow to write on database
  chmod 644 ${DATABASE_FILE}  
  
  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 
  
  echo "Start services ..."
  service memcached start 
  service php7.0-fpm start
  service nginx start  

  # show mirroring page in index
  ln -fs index_mirroring.php index.php 

  echo "Start mirroring ..."
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json | tee -a ${LOG_DIR}/mirroring.log 

  # restore index
  ln -fs index_mediawiki.php index.php 
  
  echo "Stop services ..."
  service nginx stop  
  service php7.0-fpm stop
  service memcached stop 
  
  # force to purge page cache
  touch LocalSettings.php

  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick > ${LOG_DIR}/mw_update.log 

  echo "Refresh links ..."
  su -c 'php maintenance/refreshLinks.php -e 200 --namespace 0' -s /bin/bash  www-data >> ${LOG_DIR}/mw_update.log 
   
  #To write in image dir
  chown -R www-data:www-data ${DATA_DIR}  
  
fi



if [ ${CLEAN} ]
then
  echo "Delete old revisions ..."
  php maintenance/deleteOldRevisions.php --delete  
  echo "Delete archive file ..." 
  php maintenance/deleteArchivedFiles.php --delete  
  echo "Start Mediawiki maintenance ..."
  maintenance/update.php --quick
fi

if [ ${CLEAN_IMAGES} ]
then
  echo "Delete thumb, temp and archive ..."
  rm -rvf ${DATA_DIR}/images/thumb/* ${DATA_DIR}/images/temp/* ${DATA_DIR}/images/archive/*
  cp -f ./LocalSettings.custom.origin.php ${CFG_DIR}/LocalSettings.custom.php
fi

if [ ${IMAGE_OVERSIZE} ]
then 
  find ${DATA_DIR}/images -size +${IMAGE_OVERSIZE}M -exec rm -f {} \;
fi

if [ ! ${DEBUG}  ]
then
  # ignore debug LocalSettings
  echo '<?php ?>' > ./LocalSettings.debug.php
fi

# force mediawiki index
ln -fs index_mediawiki.php index.php 

# ignore mirroring LocalSettings
echo '<?php ?>' > ./LocalSettings.mirroring.php

if [ ${GO_BASH}  ]
then
  /bin/bash
else
  start-services.sh
fi
