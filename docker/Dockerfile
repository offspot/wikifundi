FROM php:7.1-apache

MAINTAINER kiwix

# System Dependencies.
RUN apt-get update && apt-get install -y \
		git \
		imagemagick \
		libicu-dev \
		libav-tools \
		librsvg2-bin \
		poppler-utils \
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
		npm \
		# Required for SyntaxHighlighting
		python \
	--no-install-recommends && rm -r /var/lib/apt/lists/*
	
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


# Version
ENV MEDIAWIKI_MAJOR_VERSION 1.31
ENV MEDIAWIKI_VERSION 1.31.0
ENV MEDIAWIKI_RC rc.0

ENV PARSOID_VERSION_YEAR 2016
ENV PARSOID_VERSION_MONTH 08

# Config
ENV DATABASE_NAME my_wiki

# MediaWiki setup
RUN curl -fSL "https://releases.wikimedia.org/mediawiki/${MEDIAWIKI_MAJOR_VERSION}/mediawiki-${MEDIAWIKI_VERSION}-${MEDIAWIKI_RC}.tar.gz" -o mediawiki.tar.gz \
	&& tar -xz --strip-components=1 -f mediawiki.tar.gz \
	&& rm mediawiki.tar.gz \
	&& chown -R www-data:www-data extensions skins cache images
	
# Configure Mediawiki
COPY ./config/mediawiki/LocalSettings.php ./
RUN rm -rf mw-config

# Init SQLite database
RUN mkdir -p /var/www/data
COPY ./data/sqlite/${DATABASE_NAME}.sqlite /var/www/data/
RUN chown -R www-data:www-data /var/www/data

# Parsoid setup
RUN curl -fSL "http://download.kiwix.org/other/wikifundi/parsoid_${PARSOID_VERSION_YEAR}-${PARSOID_VERSION_MONTH}.tar.bz2" -o parsoid.tar.gz \
  && tar -xf parsoid.tar.gz \
  && rm parsoid.tar.gz
COPY ./config/parsoid/localsettings.js ./parsoid/
RUN chown -R www-data:www-data parsoid 
	
# Copy images
#COPY ./data/images/* images/
#RUN chown -R www-data:www-data images
	
