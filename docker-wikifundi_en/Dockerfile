FROM mw_kiwix 
ENV DATABASE_NAME mw_wikifundi_en
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./LocalSettings.custom.php
COPY ${MEDIAWIKI_LOGO_FILE} ./
COPY ${MIRRORING_CONFIG_FILE} ./mirroring.json
