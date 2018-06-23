WikiFundi
=========

WikiFundi is a solution which provide a pre-configured Mediawiki in a
similar way like Wikipedia. Probably the easiest way to train users if
you do not have access to Internet!

Install empty MediaWiki 
-----------------------
Run for english version :

```
docker run -p 8080:80 -v ${PWD}/data-init:/var/www/data -it openzim/wikifundi-en
```

For french version :

```
docker run -p 8080:80 -v ${PWD}/data-init:/var/www/data -it openzim/wikifundi-fr
```

Go to  [http://localhost:8080/](http://localhost:8080/)

Default admin logging :

* User : Admin
* Password : wikiadmin

Mirroring with WikiFundi
------------------------

You can lauch mirroring by changing environments variables MIRRORING :

`docker run -p 8080:80 -e MIRRORING=1 -v ${PWD}/data:/var/www/data -it openzim/wikifundi-en`
 
You can also change options script with MIRRORING_OPTIONS : 

* `-f, --force` : always copy  the content (even if page exist on site dest) (default : false)
* `-t, --no-sync-templates` : do not copy templates used by the pages to sync. (default : false)
* `-u, --no-upload-files` : do not copy files (images, css, js, sounds, ...) used by the pages to sync (default : false)
* `-p, --no-sync` : do not copy anything (default : false)
* `-m, --no-modify` : do not modify pages (default : false)
* `-r, --resume` : try to resume previous sync (default : false)
* `-e, --export-dir <directory>` : write resume files in this directory (default : current directory)
* `-w, --thumbwidth` :try to download thumbnail image with this width instead original image (default : 1024)
* `-s, --maxsize` : do not files download greater to this limit (default : 100MB)
* `-a, --async` : execute mirroring in async mode (5 threads / cpu). No works with SQLITE database. (default : false)
  
Case usaging :

* `MIRRORING_OPTIONS='-m 5MB -w 2000'` : sync page, templates, files and modify pages. Do not copy file > 5MB and Copy images (jpeg and png) in 2000px (if available).
* `MIRRORING_OPTIONS='-tu'` : sync and modify pages. Do not copy dependances (templates and files).
* `MIRRORING_OPTIONS='-p'` : just modify pages.
* `MIRRORING_OPTIONS='-pm'` : do anything.
* `MIRRORING_OPTIONS=-'af'` : copy all pages and their dependencies in async mode.
 
After mirroring, you can generate tarball by going [http://localhost:8080/export_data.php](http://localhost:8080/export_data.php). A README file is in this tarball to explain an installation without Docker.

Build your Docker image
-----------------------
The WikiFundi image extends the `openzim/mediawiki` Docker image to
allow mirroring a existing wiki (by example Wikipedia) and
use this wiki offline.

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
docker run -p 8080:80 -v ${PWD}/data:/var/www/data -it wikifundi_en
```
As french version, yon can extend openzim/wikifundi-en to create an image for other Wikipedia language or other wiki.
