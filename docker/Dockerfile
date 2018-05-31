#APACHE+PHP
FROM php:7.1-apache

#
# Author : Florent Kaisser <florent.pro@kaisser.name>
#
LABEL maintainer="kiwix"

# Volumes to store database and medias (images...) files
VOLUME /var/www/html/images
VOLUME /var/www/data

# Wiki name
ENV WIKI_NAME kiwix 

# Database name
ENV DATABASE_NAME mw_kiwix

# Files config
ENV MEDIAWIKI_CONFIG_FILE_CUSTOM ./config/mediawiki/LocalSettings.custom.php
ENV MEDIAWIKI_CONFIG_FILE_BASE ./config/mediawiki/LocalSettings.php
ENV MEDIAWIKI_CONFIG_FILE_COMPOSER ./config/mediawiki/composer.json
ENV PARSOID_CONFIG_FILE ./config/parsoid/config.yaml
ENV PYWIKIBOT_CONFIG_FILE ./config/pywikibot/user-config.py
ENV PYWIKIBOT_PASSWORD_FILE ./config/pywikibot/user-password.py
ENV MIRRORING_CONFIG_FILE ./config/mirroring/mirroring.json

# Custom image
ENV MEDIAWIKI_LOGO_FILE ./assets/images/logo.png

# Media Wiki Version
ENV MEDIAWIKI_MAJOR_VERSION 1.31
ENV MEDIAWIKI_VERSION 1.31.0
ENV MEDIAWIKI_RC rc.0
ENV MEDIAWIKI_EXT_VERSION REL1_31

# PyWikibot fileconfig directory
ENV PYWIKIBOT2_DIR /usr/local/etc

###################
# SOFTWARES SETUP #
###################

# add repos to install nodejs
RUN apt-get update && apt-get install gnupg \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - 

# System Dependencies.
RUN apt-get install -y \
		  git \
		  vim \
		  unzip \
		  imagemagick \
		  libicu-dev \
		  libav-tools \
		  librsvg2-bin \
		  poppler-utils \
		  memcached \
		  # Required for Math renderer
		  texlive \		
      texlive-fonts-recommended \ 
      texlive-lang-greek \ 
      texlive-latex-recommended	\			
      build-essential \ 
      dvipng ocaml \ 
      cjk-latex \
		  # Required for Parsoid
		  redis-server \
		  nodejs \
		  # Ruired for Scribunto
		  lua5.1 \
		  # Required for SyntaxHighlighting
		  python3 \
		  # to generate locales
		  locales \
	  --no-install-recommends && rm -r /var/lib/apt/lists/*
	
# generate locale (set locale is used by MediaWiki scripts)
RUN {  echo "LANG=en_US.UTF-8"; \
       echo "LC_ALL=en_US.utf8"; \
} > /etc/default/locale && locale-gen en_US.UTF-8
	
# Install the PHP extensions we need
# mysqli needed for sqlite
RUN docker-php-ext-install mbstring mysqli opcache intl

# Install the default object cache.
RUN pecl channel-update pecl.php.net \
	&& pecl install apcu-5.1.8 \
	&& docker-php-ext-enable apcu

# set recommended PHP.ini settings
# see https://secure.php.net/manual/en/opcache.installation.php
RUN { \
		echo 'opcache.memory_consumption=128'; \
		echo 'opcache.interned_strings_buffer=8'; \
		echo 'opcache.max_accelerated_files=4000'; \
		echo 'opcache.revalidate_freq=60'; \
		echo 'opcache.fast_shutdown=1'; \
		echo 'opcache.enable_cli=1'; \
	} > /usr/local/etc/php/conf.d/opcache-recommended.ini

# MediaWiki setup
RUN curl -fSL "https://releases.wikimedia.org/mediawiki/${MEDIAWIKI_MAJOR_VERSION}/mediawiki-${MEDIAWIKI_VERSION}-${MEDIAWIKI_RC}.tar.gz" -o mediawiki.tar.gz \
	&& tar -xz --strip-components=1 -f mediawiki.tar.gz \
	&& rm mediawiki.tar.gz \
	&& chown -R www-data:www-data skins cache images

# Parsoid setup
RUN git clone --quiet https://gerrit.wikimedia.org/r/p/mediawiki/services/parsoid \
  # install modules
  && cd parsoid \
  && npm install \
  && cd .. \
  # update node
  && npm cache clean -f \
  && npm install -g n \
  && n stable 

RUN chown -R www-data:www-data parsoid 

######################################################
# ADD MEDIAWIKI EXTENSIONS NEEDED BY MEDIAWIKI/KIWIX #
######################################################

# Copy script to add an extension
COPY ./add_mw_extension.py /usr/local/bin/add_mw_extension
RUN chmod a+x /usr/local/bin/add_mw_extension

# Call script to add all extensions needed by MediaWiki/Kiwix
RUN add_mw_extension Nuke ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension Scribunto ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension UploadWizard ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension TitleKey ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension TitleBlacklist ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension MwEmbedSupport ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension TimedMediaHandler ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension wikihiero ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension Math ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension timeline ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension Echo ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension MobileFrontend ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension Thanks ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension VisualEditor ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension EventLogging ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension GuidedTour ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension Wikibase ${MEDIAWIKI_EXT_VERSION}
RUN add_mw_extension GeoData ${MEDIAWIKI_EXT_VERSION}

# To install Maps and Validator extensions with composer
COPY ${MEDIAWIKI_CONFIG_FILE_COMPOSER} ./
RUN curl -fSL https://getcomposer.org/composer.phar -o composer.phar \
 && php composer.phar update --no-dev

# Install MetaDescriptionTag extension from GitHub beacause it is not in official repository
RUN curl -fSL https://github.com/kolzchut/mediawiki-extensions-MetaDescriptionTag/archive/master.zip -o MetaDescriptionTag.zip \
 && unzip MetaDescriptionTag.zip -d extensions/ \
 && mv extensions/mediawiki-extensions-MetaDescriptionTag-master extensions/MetaDescriptionTag

# Clean Math extension
RUN make -C extensions/Math/math clean all \
 && make -C extensions/Math/texvccheck clean all

# Fix owner
RUN chown -R www-data:www-data extensions

##########################
# FINALIZE CONFIGURATION #
##########################

# Configure Mediawiki
COPY ${MEDIAWIKI_CONFIG_FILE_BASE} ./LocalSettings.php
COPY ${MEDIAWIKI_CONFIG_FILE_CUSTOM} ./LocalSettings.custom.php

# Configure Parsoid
COPY ${PARSOID_CONFIG_FILE} ./parsoid/

# Configure Pywikibot (must be in same directory of wikimedia_sync.py)
COPY ${PYWIKIBOT_CONFIG_FILE} ${PYWIKIBOT2_DIR}/ 
COPY ${PYWIKIBOT_PASSWORD_FILE} ${PYWIKIBOT2_DIR}/ 

# Configure Wikifundi config
COPY ${MIRRORING_CONFIG_FILE} ./mirroring.json

# Copy assets
COPY ${MEDIAWIKI_LOGO_FILE} ./

# Needed to init database
COPY ./data/my_wiki.sqlite /tmp/

# Remove configuration by web
#RUN rm -rf mw-config

###########
# START ! #
###########

# Copy script used by start.sh to sync wikimedia pages
COPY ./wikimedia_sync.py /usr/local/bin/wikimedia_sync
RUN chmod a+x /usr/local/bin/wikimedia_sync
  
# Run start script
COPY ./start.sh /usr/local/bin/start.sh
RUN chmod a+x /usr/local/bin/start.sh
ENTRYPOINT "start.sh"
