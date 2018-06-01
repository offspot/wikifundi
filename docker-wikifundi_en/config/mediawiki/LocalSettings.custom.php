<?php

# General
$wgLanguageCode     = "en";
$wgSitename         = "Kiwix";

# Site language 
$wgLanguageCode = "en";
$wgUploadWizardConfig['uwLanguages'] = array( 'en' => 'English' );

# Database settings
$wgDBtype        = "sqlite";
$wgDBserver      = "";
$wgDBname        = "mw_wikifundi_en";
$wgDBuser        = "";
$wgDBpassword    = "";
$wgSQLiteDataDir = "/var/www/data";

$wgVirtualRestConfig['modules']['parsoid'] = array(
						   'url' => 'http://wikifundi-en.sloppy.zone:8000',
						   'domain' => 'wikifundi-en.sloppy.zone',
						   'prefix' => 'mediawiki_kiwix',
						   'forwardCookies' => true
						   );

?>
