FROM openzim/wikifundi-en

ENV DATABASE_NAME mw_wikifundi_fr

# Configure MediaWiki
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./LocalSettings.custom.php

# Copy the Mirroring Script
COPY ${MIRRORING_CONFIG_FILE} ./mirroring.json

