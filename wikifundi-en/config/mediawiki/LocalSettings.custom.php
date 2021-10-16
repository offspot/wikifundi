<?php

# General
$wgSitename         = "WikiFundi";
$wgNamespacesToBeSearchedDefault = [
	NS_MAIN => true,
	NS_PROJECT => true,
	NS_CATEGORY => true,
	4 => true,
	NS_HELP => true,
	NS_USER => true,
];

# Site language
$wgLanguageCode = "en";
$wgULSLanguageDetection = false; // don't detect user agent language
$wgUploadWizardConfig['uwLanguages'] = [ 'en' => 'English' ];
$wgUploadWizardConfig['tutorial']['skip'] = true;

# Database settings
$wgDBtype        = "sqlite";
$wgDBserver      = "";
$wgDBname        = "mw_wikifundi_en";
$wgDBuser        = "";
$wgDBpassword    = "";
$wgSQLiteDataDir = "/var/www/data";

# Custom logo
$wgLogo = "/logo.png";

# License
$wgRightsUrl = null;
$wgRightsPage = null;
$wgRightsText = null;
$wgRightsIcon = "/A_WikiAfrica_project.png";

# Uploads
ini_set('memory_limit', '512M');
ini_set('post_max_size', '5M');
ini_set('upload_max_filesize', '5M');
$wgMaxUploadSize = 1024*1024*5;

$wgHooks['SkinTemplateOutputPageBeforeExec'][] = function( $sk, &$tpl ) {
	$tpl->set( 'contact', $sk->footerLink( 'contact', 'contactpage' ) );
	$tpl->data['footerlinks']['places'][] = 'contact';
	return true;
};

$wgHooks['SkinTemplateOutputPageBeforeExec'][] = function( $sk, &$tpl ) {
	$tpl->set( 'credit', $sk->footerLink( 'credit', 'creditpage' ) );
	$tpl->data['footerlinks']['places'][] = 'credit';
	return true;
};

require_once("$IP/LocalSettings.mirroring.php");
require_once("$IP/LocalSettings.debug.php");

$wgPasswordPolicy = [ 'policies' => [ 'default' => [] ], 'checks' => [] ];

?>
