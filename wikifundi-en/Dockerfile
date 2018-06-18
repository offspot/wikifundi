FROM openzim/mediawiki

ENV PYWIKIBOT_CONFIG_FILE ./config/pywikibot/user-config.py
ENV MIRRORING_CONFIG_FILE ./config/mirroring/mirroring.json
ENV README_FILE ./assets/docs/README
ENV PYWIKIBOT2_DIR /usr/local/etc

# Custom image
ENV MEDIAWIKI_LOGO_FILE ./assets/images/logo.png

ENV DATABASE_NAME mw_wikifundi_en

# Install PyWikiBot library
RUN apt-get update \
   && apt-get install -y --no-install-recommends python3-pip \
   && pip3 install -U setuptools \
   && pip3 install pywikibot
   
# Configure Pywikibot (must be in same directory of wikimedia_sync.py)
COPY ${PYWIKIBOT_CONFIG_FILE} ${PYWIKIBOT2_DIR}/ 

# Configure MediaWiki
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./LocalSettings.custom.php
COPY ${MEDIAWIKI_LOGO_FILE} ../
COPY ${README_FILE} ./ 

# Configure Parsoid with specific domain
COPY ${PARSOID_CONFIG_FILE} ./parsoid/

# Copy the Mirroring Script
COPY ${MIRRORING_CONFIG_FILE} ./mirroring.json

# Generate Passord file for pywikibot
RUN { \
 echo "# -*- coding: utf-8 -*-" ; \
 echo "(u'Admin', u'${MEDIAWIKI_ADMIN_PASSWORD}')" ; \
} > ${PYWIKIBOT2_DIR}/user-password.py \
 &&  chmod 700 ${PYWIKIBOT2_DIR}/user-password.py 

# Copy script used by start.sh to sync wikimedia pages
COPY ./wikimedia_sync.py /usr/local/bin/wikimedia_sync
RUN chmod a+x /usr/local/bin/wikimedia_sync

#ENTRYPOINT /bin/bash

# Run start script
COPY ./start.sh /usr/local/bin/start.sh
RUN chmod a+x /usr/local/bin/start.sh
ENTRYPOINT "start.sh"
