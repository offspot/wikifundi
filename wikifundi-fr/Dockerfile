FROM ghcr.io/offspot/wikifundi-en
LABEL org.opencontainers.image.source https://github.com/offspot/wikifundi

ENV DATABASE_NAME mw_wikifundi_fr

# Configure MediaWiki
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./

# Copy the mirroring file config
COPY ${MIRRORING_CONFIG_FILE} ./
COPY ${MIRRORING_DELETE_FILE} ./
