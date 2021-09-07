FROM ghcr.io/offspot/wikifundi-en
LABEL org.opencontainers.image.source https://github.com/offspot/wikifundi

ENV DATABASE_NAME mw_wikifundi_es
ENV MIRRORING_CONFIG_FILE2 ./config/mirroring/mirroring2.json

# Configure MediaWiki
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./LocalSettings.custom.php

# Copy the mirroring file config
COPY ${MIRRORING_CONFIG_FILE} ./mirroring.json
COPY ${MIRRORING_CONFIG_FILE2} ./mirroring2.json
COPY ${MIRRORING_DELETE_FILE} ./
