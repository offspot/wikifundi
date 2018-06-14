#!/bin/sh

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite

if [ ! -e ${DATABASE_FILE} ]
then 
  # if new databse, always mirroring
  export MIRRORING=1  
fi

mediawiki-init.sh

ln -s ${DATA_DIR} data

if [ ${MIRRORING} ]
then
  #mirroring
  service nginx start
  service php7.0-fpm start
  service memcached start 
  echo "Starting mirroring ..."
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json | tee -a ${LOG_DIR}/mirroring.log 
  service memcached stop
  service php7.0-fpm stop
  service nginx stop
  
  maintenance
  
  php maintenance/refreshLinks.php -e 100 >> ${LOG_DIR}/mw_update.log 
  
  #build tarbals
  #echo "Build tarbal"
  #cd ${DATA_DIR}
  #tar -czvvf data-${DATABASE_NAME}.tgz ${DATABASE_NAME}.sqlite log config >> ${LOG_DIR}/mirroring.log 
  #tar -cvvf images-${DATABASE_NAME}.tar images >> ${LOG_DIR}/mirroring.log 
  #cd ../html
fi

start-services.sh

