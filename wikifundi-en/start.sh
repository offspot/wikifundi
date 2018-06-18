#!/bin/sh

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
README_FILE=${DATA_DIR}/README

cp README ${README_FILE} 

if [ ! -e ${DATABASE_FILE} ]
then 
  # if new databse, always mirroring
  export MIRRORING=1  
fi

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
  php maintenance/refreshLinks.php -e 1000 >> ${LOG_DIR}/mw_update.log 
 
  #build tarbals
  #echo "Build tarbal"
  #cd ${DATA_DIR}
  #tar -czvvf data-${DATABASE_NAME}.tgz ${DATABASE_NAME}.sqlite log config >> ${LOG_DIR}/mirroring.log 
  #tar -cvvf images-${DATABASE_NAME}.tar images >> ${LOG_DIR}/mirroring.log 
  #cd ../html

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

