#!/bin/bash
#
# add_mw_extension.sh
#
# Add an extension to MediaWiki from a repository
#
# Usage : ./add_mw_extension.sh <extension> <version>
#

REPOSITORY='https://extdist.wmflabs.org/dist/extensions'
MEDIAWIKI_PATH='/var/www/html/'
NAME=$1
VERSION=$2

if [ $# -ne 2 ]
  then
    echo "Need two args"
    exit 1
fi

echo "Add ${NAME} extension"

cd ${MEDIAWIKI_PATH}/extensions

curl -fSL ${REPOSITORY}/${NAME}-${VERSION}.tar.gz -o ${NAME}.tgz \
  && tar -xf ${NAME}.tgz \
  && rm ${NAME}.tgz


