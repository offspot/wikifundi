WikiFundi
=========

WikiFundi is a solution which provide a pre-configured Mediawiki in a
similar way like Wikipedia. Probably the easiest way to train users if
you do not have access to Internet!

Here steps to install it with Docker or on a RaspberryPi.

Mirroring with WikiFundi
------------------------

The WikiFundi image extends the `openzim/mediawiki` Docker image to
allow mirroring a existing wiki (by example Wikipedia) and
use this wiki offline

The config files are located in `config` directory.

This directory contain the configuration of :

* `mirroring/mirroring.json` : 
    Pages to copy from an other wiki and modifications after copy. 
    To get file structure :
      ```
        export PYWIKIBOT2_DIR=config/pywikibot/`
        ./wikimedia_sync.py --help
      ```
* `mediawiki/LocalSettings.custom.php` : 
    You can customise the Mediawiki by editing your this file. 
    If you want to know more, have a look to [documentation](https://www.mediawiki.org/wiki/Manual:LocalSettings.php)
* `parsoid/config.yaml` :
    Parsoid config file (allow to use VisualEdit)
* `pywikibot/user-config.py` :
    [Configure pywikibot library](https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py) to use MediaWiki API (needed for mirroring)


You can also customize your logo in `assets/images` as customize the `assets/docs/README` embeded with data 

To build and run :

```
mkdir -p data
docker build -t wikifundi_en .
sudo docker run -p 8080:80 -v ${PWD}/data:/var/www/data -it wikifundi_en
```
  
On start, if the database not exist, then it is initialized. You can 
lauch mirroring by changing environments variables :

`sudo docker run -p 8080:80 -e MIRRORING=1 -v ${PWD}/data:/var/www/data -it wikifundi_en`
 
You can also change options script with MIRRORING_OPTIONS : 

* -f, --force : always copy  the content (even if page exist on site dest) (default : false).
* -t, --no-sync-templates : do not copy templates used by the pages to sync. Involve no-sync-dependances-templates (default : false).
* -d, --no-sync-dependances-templates : do not copy templates used by templates (default : false).
* -u, --no-upload-files : do not copy files (images, css, js, sounds, ...) used by the pages to sync (default : false).
* -p, --no-sync : do not copy anything. If not -m, just modify (default : false).
* -m, --no-modify : do not modify pages (default : false).
* -e, --export-dir <directory> : write json export files in this directory
* -w, --thumbwidth :try to download thumbnail image with this width instead original image (default : 2000)
* -s, --maxsize : do not files download greater to this limit (default : 100MB)
* -a, --async : execute mirroring in async mode (5 threads / cpu). No works with SQLITE database. (default : false)

To Mirroring without templates dependences  :

 `sudo docker run -p 8080:80 -e MIRRORING=1 -e MIRRORING_OPTIONS="-d" -v ${PWD}/data:/var/www/data -it wikifundi_en`
 
Go to  [http://localhost:8080/](http://localhost:8080/)

Default admin logging :

* User : Admin
* Password : wikiadmin
 
After mirroring, you can generate tarball by going [http://localhost:8080/export_data.php](http://localhost:8080/export_data.php)



