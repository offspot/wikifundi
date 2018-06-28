FROM openzim/wikifundi-en

ENV DATABASE_NAME mw_wikifundi_fr

# Configure MediaWiki
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./

# Copy the mirroring file config 
COPY ${MIRRORING_CONFIG_FILE} ./

