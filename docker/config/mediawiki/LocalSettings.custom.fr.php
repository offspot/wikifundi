<?php

# General
$wgLanguageCode     = "fr";
$wgSitename         = "WikiFundi";

# Database settings
$wgDBtype        = "sqlite";
$wgDBserver      = "";
$wgDBname        = "mw_fr_africapack";
$wgDBuser        = "";
$wgDBpassword    = "";
$wgSQLiteDataDir = "/var/www/data";

# Entropy
$wgSecretKey = "d5eb60c72d9fa0946adcfb1cb55cd66c654a093df0a63946d32d645f38a5eb19";

# Wikipedia namespace
define("NS_FOO", 3000);
define("NS_FOO_TALK", 3001);
$wgExtraNamespaces[NS_FOO] = "Wikipédia";
$wgExtraNamespaces[NS_FOO_TALK] = "Wikipédia_talk"; // Note underscores in the namespace name.

# Not limit for attempting to login
$wgPasswordAttemptThrottle = false;

# Allow to put __NOINDEX__ on all pages
$wgExemptFromUserRobotsControl = array();

# Allow JS for users
$wgUseSiteJs = true;
$wgUserSiteJs = true;
$wgAllowUserJs = true;

# Allow heavy template
$wgMaxArticleSize = 10000;
$wgExpensiveParserFunctionLimit = 10000;
$wgAllowSlowParserFunctions = true;

# Necessary if you use nginx as reverse proxy
$wgUsePrivateIPs = true;
$wgSquidServersNoPurge = array('127.0.0.1');

# Avoid blocked users to login
$wgBlockDisablesLogin = true;

# The following permissions were set based on your choice in the installer
$wgGroupPermissions['*']['createaccount'] = true;
$wgGroupPermissions['*']['edit'] = false;

# Upload file allowed extension
$wgFileExtensions = array_merge( $wgFileExtensions, array( 'zip', 'ogg', 'webm' ) );

# Hieroglyphs
wfLoadExtension( 'wikihiero' );

# Maths
wfLoadExtension('Math');

# Timeline
putenv("GDFONTPATH=/usr/share/fonts/truetype/freefont");
wfLoadExtension( 'timeline' );


# Echo extension
wfLoadExtension( 'Echo' );

# Mobile frontend
wfLoadExtension( 'MobileFrontend' );
$wgMFAutodetectMobileView = true;

# Thanks
wfLoadExtension( 'Thanks' );

# Visual Editor
wfLoadExtension( 'VisualEditor' );
$wgDefaultUserOptions['visualeditor-enable'] = 1;
$wgVisualEditorNamespaces[] = NS_PROJECT;
$wgVirtualRestConfig['modules']['parsoid'] = array(
						   'url' => 'http://localhost:8000',
						   'domain' => 'fr.africapack.kiwix.org',
						   'prefix' => 'fr_africapack',
						   'forwardCookies' => true
						   );

?>
