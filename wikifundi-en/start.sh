#!/bin/bash

LOG_DIR=${DATA_DIR}/log
DATABASE_FILE=${DATA_DIR}/${DATABASE_NAME}.sqlite
README_FILE=${DATA_DIR}/README
CFG_DIR=${DATA_DIR}/config

cp README ${README_FILE}

handle-htpassword-opt.sh
service memcached start
mediawiki-init.sh

ln -s ${DATA_DIR} data

if [ ${MIRRORING} ]
then
  echo "Setting-up mirroring…"

  echo "> Creating “bot” user"
  php maintenance/createAndPromote.php --bureaucrat --sysop --bot --force botimport $MEDIAWIKI_ADMIN_PASSWORD

  echo "> Fixing permissions on ${DATABASE_FILE}"
  chmod 644 ${DATABASE_FILE}

  echo "> Disabling MW standard use"
  ln -fs index_mirroring.php index.php

  echo "> Starting Mediawiki"
  service php7.3-fpm start
  service nginx start

  echo "> Mirroring ..."
  wikimedia_sync ${MIRRORING_OPTIONS} -e "${LOG_DIR}" mirroring.json 2>&1 | tee -a ${LOG_DIR}/mirroring.log

  echo "> Restoring MW standard use"
  ln -fs index_mediawiki.php index.php

  echo "> Stopping Mediawiki"
  service nginx stop
  service php7.3-fpm stop

  echo "> Deleting extra pages"
  php maintenance/deleteBatch.php  --conf ./LocalSettings.php -u botimport -r "No needed for Wikifundi" ./deleteBatch.txt

  echo "> Purging local cache"
  touch LocalSettings.php

  echo "> Running MW maintenance"
  php maintenance/update.php --quick > ${LOG_DIR}/mw_update.log

  echo "> Refreshing links"
  su -c 'php maintenance/refreshLinks.php -e 200 --namespace 0' -s /bin/bash  www-data >> ${LOG_DIR}/mw_update.log

  echo "> Emptying recentchanges table"
  sqlite3 ${DATABASE_FILE} "DELETE FROM recentchanges;"

  echo "> Fixing permissions on ${DATA_DIR}"
  chown -R www-data:www-data ${DATA_DIR}
fi

if [ ${CLEAN} ]
then
  echo "Cleaning-up database..."

  echo "> Deleting old revisions"
  php maintenance/deleteOldRevisions.php --delete

  echo "> Deleting archived files"
  php maintenance/deleteArchivedFiles.php --delete

  echo "> Running MW maintenance"
  maintenance/update.php --quick
fi

if [ ${CLEAN_IMAGES} ]
then
  echo "Cleaning-up images (thumb/, temp/, archive/)..."
  rm -rvf ${DATA_DIR}/images/thumb/* ${DATA_DIR}/images/temp/* ${DATA_DIR}/images/archive/*
  cp -f ./LocalSettings.custom.origin.php ${CFG_DIR}/LocalSettings.custom.php
fi

if [ ${IMAGE_OVERSIZE} ]
then
  echo "Removing oversized (>${IMAGE_OVERSIZE}M) images..."
  find ${DATA_DIR}/images -size +${IMAGE_OVERSIZE}M -exec rm -f {} \;
fi

if [ ! ${DEBUG}  ]
then
  echo "Disabling debug settings"
  echo '<?php ?>' > ./LocalSettings.debug.php
fi

ln -fs index_mediawiki.php index.php

echo "Disabling mirroring settings"
echo '<?php ?>' > ./LocalSettings.mirroring.php

if [ ${GO_BASH}  ]
then
  /bin/bash
else
  service php7.3-fpm start && \
  service cron start

  echo "Starting…"
  exec "$@"
fi
