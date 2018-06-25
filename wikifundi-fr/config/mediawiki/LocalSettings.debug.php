<?php

# Debug
error_reporting( -1 );
ini_set( 'display_errors', 1 );
$wgShowExceptionDetails=true;
$wgShowDBErrorBacktrace = true;
$wgDebugToolbar=true;
$wgShowDebug=true;
$wgDevelopmentWarnings=true;

# General
$wgLanguageCode     = "fr";
$wgSitename         = "WikiFundi";

# Site language 
$wgLanguageCode = "fr";
$wgUploadWizardConfig['uwLanguages'] = array( 'fr' => 'French' );

# Database settings
$wgDBtype        = "sqlite";
$wgDBserver      = "";
$wgDBname        = "mw_wikifundi_fr";
$wgDBuser        = "";
$wgDBpassword    = "";
$wgSQLiteDataDir = "/var/www/data";

# Custom logo
$wgLogo = "/logo.png";

# Uploads
ini_set('memory_limit', '512M');
ini_set('post_max_size', '5M');
ini_set('upload_max_filesize', '5M');
$wgMaxUploadSize = 1024*1024*5;

?>
