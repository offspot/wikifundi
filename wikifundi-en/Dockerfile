FROM ghcr.io/offspot/mediawiki:1.43.11
LABEL org.opencontainers.image.source https://github.com/offspot/wikifundi

ENV PYWIKIBOT_CONFIG_FILE ./config/pywikibot/user-config.py
ENV MIRRORING_CONFIG_FILE ./config/mirroring/mirroring.json
ENV MIRRORING_DELETE_FILE ./config/mirroring/deleteBatch.txt
ENV README_FILE ./assets/docs/README
ENV PYWIKIBOT_DIR /usr/local/etc

# Custom image
ENV MEDIAWIKI_LOGO_FILE ./assets/images/logo.png
ENV MEDIAWIKI_LICENCE ./assets/images/A_WikiAfrica_project.png
ENV MEDIAWIKI_CONF_MIRRORING ./config/mediawiki/LocalSettings.mirroring.php
ENV MEDIAWIKI_CONF_DEBUG ./config/mediawiki/LocalSettings.debug.php

ENV DATABASE_NAME mw_wikifundi_en

# Specific default admin password
ENV MEDIAWIKI_ADMIN_PASSWORD adminadmin

# Install PyWikiBot library
RUN apt-get update \
   && apt-get install -y --no-install-recommends python3-pip ghostscript \
   && pip3 install --no-cache-dir --break-system-packages --ignore-installed -U setuptools wheel \
   && pip3 install --no-cache-dir --break-system-packages "mwparserfromhell==0.7.2" \
   && pip3 install --no-cache-dir --break-system-packages "pywikibot==11.9.0"

# Configure PHP-fpm
COPY config/php-fpm/*.conf /etc/php/8.4/fpm/pool.d/

# Configure Pywikibot (must be in same directory of wikimedia_sync.py)
COPY ${PYWIKIBOT_CONFIG_FILE} ${PYWIKIBOT_DIR}/

# Configure MediaWiki
WORKDIR /var/www/html/w
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./LocalSettings.custom.php
COPY ${MEDIAWIKI_LOGO_FILE} ../
COPY ${MEDIAWIKI_LICENCE} ../
COPY ${MEDIAWIKI_CONF_MIRRORING} ./
COPY ${MEDIAWIKI_CONF_DEBUG} ./
COPY ${README_FILE} ./


# Copy the Mirroring Script
COPY ${MIRRORING_CONFIG_FILE} ./mirroring.json
COPY ${MIRRORING_DELETE_FILE} ./

# Generate Passord file for pywikibot
RUN printf "# -*- coding: utf-8 -*-\n(\"botimport\", \"${MEDIAWIKI_ADMIN_PASSWORD}\")\n" \
  > ${PYWIKIBOT_DIR}/user-password.py \
  &&  chmod 600 ${PYWIKIBOT_DIR}/user-password.py

# Allow to avoid thumbs generation error with error in a PDF
RUN { \
  mv /usr/bin/gs /usr/bin/gs9-20 ; \
  echo '/usr/bin/gs9-20 -sstdout=%stderr $@' > /usr/bin/gs ; \
  chmod a+x /usr/bin/gs ; \
}

# Fix Echo extension's SQLite migration patch: it uses MySQL's
# "auto_increment" (invalid SQLite syntax) and a MySQL-only index
# prefix-length suffix, instead of the valid SQLite forms used by the
# extension's own generated schema (sql/sqlite/tables-generated.sql).
# Unfixed upstream as of 2026-10: https://github.com/wikimedia/mediawiki-extensions-Echo/blob/master/sql/sqlite/patch-cleanup-push_subscription-foreign-keys-indexes.sql
RUN sed -i \
  -e 's/eps_id INT UNSIGNED NOT NULL PRIMARY KEY auto_increment,/eps_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,/' \
  -e 's/(eps_token(10))/(eps_token)/' \
  extensions/Echo/sql/sqlite/patch-cleanup-push_subscription-foreign-keys-indexes.sql

# Copy script used by start.sh to sync wikimedia pages
COPY ./wikimedia_sync.py /usr/local/bin/wikimedia_sync
RUN chmod a+x /usr/local/bin/wikimedia_sync

COPY ./export_data.php ../

COPY ./index_mirroring.php ./
RUN mv index.php index_mediawiki.php

# Run start script
COPY ./start.sh /usr/local/bin/start.sh
RUN chmod a+x /usr/local/bin/start.sh
ENTRYPOINT ["start.sh"]
CMD ["nginx", "-g", "daemon off;"]
