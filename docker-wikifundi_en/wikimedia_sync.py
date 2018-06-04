#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# author : Florent Kaisser
# maintainer : kiwix

"""
 wikimedia_sync.py
 
 Copy WikiMedia pages from a Wiki source (ex : a Wikipedia) to a Wiki 
 destionation (like a third-party wikis).

 A config file given in args contain name of pages and categories to 
 synchronize, and Wiki source and destination. 

 usage : ./wikimedia_sync.py [options] config_file1.json, config_file2.json, ...
 
 options :
  -f, --force : always copy  the content (even if page exist on site dest). Default : False
  -t, --no-sync-templates : do not copy templates used by the pages to sync. Involve no-sync-dependances-templates. Default : False
  -d, --no-sync-dependances-templates : do not copy templates used by templates.  Default : False
  -u, --no-upload-files : do not copy files (images, css, js, sounds, ...) used by the pages to sync. Default : False
  -e, --export-dir <directory> : write json export files in this directory
  
 json file config :
   
   {
    //the site must be configured in user-config.py file (see below)
    "sites":{ 
      "src":{ //set the site where to get the pages. 
        "fam": "wikipedia",
        "code": "en"
      },
      "dst":{ //set the site where to copy the pages
        "fam": "kiwix",
        "code": "en"    
      }
    },

    // list of page to copy
    "pages":[
     "Page1",
     "Page2"
     "MediaWiki:Common.css",
     "MediaWiki:Vector.js",
     ...
    ],
    
    // list of categories to copy
    "categories":[
      {
        "title":"Category 1",
        "namespace":0,
        "recurse":1
      },
      {
        "title":"Category 2",
        "namespace":4,
        "recurse":0
      }
      ...
    ]
    
    // list of modification on dest after copy
    "modifications":[
      {
        "pages":"RegEx1",
        "substitutions":[
          {
            "pattern":"Pattern 1",
            "repl":"Remplacement 1"
          },
          {
            "pattern":"Pattern 2",
            "repl":"Remplacement 2"
          }        
        ]
      },
      {
        "pages":"RegEx2",
        "substitutions":[
          {
            "pattern":"Pattern 3",
            "repl":"Remplacement 3"
          }     
        ]
      }      
    ]
  }

 IMPORTANT : We must have user-password.py and user-config.py in same 
 directory of this script or set PYWIKIBOT2_DIR to congigure pywikibot. 
 See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
"""

# To use WikiMedia API
from pywikibot import Site,Page,FilePage,Category,logging

# To load JSON file config and check options
import sys
import json
import getopt

# To use regular expression
import re

DEFAULT_OPTIONS = dict(
    force = False, 
    templatesSync = True, 
    templatesDepSync = True, 
    filesUpload = True,
    exportDir = "."    
)

def exportPagesTitle(pages, fileName, directory):
  with open("%s/mirroring_export_%s.json" % (directory,fileName), 'w',encoding='utf-8') as f:
      f.write(json.dumps(pages, sort_keys=True, indent=4,ensure_ascii=False))
      
def importPagesTitle(fileName, directory):
  with open("%s/mirroring_export_%s.json" % (directory,fileName), 'r', encoding='utf-8') as f:
      return json.load(f)
  return []  
  
def mapTitle(pages) : 
  return [ p.title() for p in pages ]  
    
def getTemplatesFromPages(siteSrc, pages) :
  templates = []
  nbPage = len(pages)
  for i,p in enumerate(pages) :
    # get templates used by p
    tplt = Page(siteSrc, p).templates()
    nbTplt = len(tplt)
    if(nbTplt > 0):
      print ("%i/%i Process %s : %i templates found " % 
              (i+1,nbPage,p.encode('utf-8'),nbTplt))
      sys.stdout.flush()
      templates.extend(mapTitle(tplt))
      
  # apply set() to delete duplicate
  return list(set(templates))  
  
def getFilesFromPages(siteSrc, pages) :
  files = []
  nbPage = len(pages)
  for i,p in enumerate(pages) :
    # get files used by p
    f = list(Page(siteSrc, p).imagelinks())
    nbFiles = len(f)
    if(nbFiles > 0):
      print ("%i/%i Process %s : %i files found" % 
               (i+1,nbPage,p.encode('utf-8'),nbFiles))
      sys.stdout.flush()
      files.extend(mapTitle(f)) 
      
  # apply set() to delete duplicate
  return list(set(files))
  
def modifyPage(dst, pageTitle, subs)  :

  try:
    p = Page(dst, pageTitle)
    
    for s in subs :
      pattern = s[0]
      repl = s[1]
      p.text = re.sub(pattern, repl, p.text)
      
    print ("Save %s" % pageTitle.encode('utf-8'))
    return dst.editpage(p)
    
  except Exception as e:
      print ("Error to modify page %s (%s)" % 
        (pageTitle.encode('utf-8'), e))
      return False
  
  
def syncPage(src, dst, pageTitle, force = False, checkRedirect = True):
  """Synchronize ONE wiki pages from src to dst
  
     return true if success
  """
  
  # init page on src and dst
  p = Page(src, pageTitle)
  newPage = Page(dst, pageTitle)
  
  try:      
    # if page exist on dest and no force -> do not sync this page
    if((not force) and newPage.exists()):  
      return False
      
    # sometime, pywikibot return a page in a different site, 
    # here check this
    elif(newPage.site == dst):
    
      #sync also the redirect target 
      if(p.isRedirectPage()):
        syncPage(src, dst, p.getRedirectTarget().title(), force, False)
        
      # copy the content of the page
      newPage.text = p.text
      
      # commit the new page on dest wiki
      return dst.editpage(newPage)
      
  except Exception as e:
    print ("Error on sync page %s (%s)" 
              % (pageTitle.encode('utf-8'), e))
    return False
    
  return False
  
def modifyPages(dst, pages, subs) :  
  nbModPage = 0
  nbPage = len(pages)
  
  for i,pageTitle in enumerate(pages):
    print ("%i/%i Modification of %s " % 
      (i+1,nbPage,pageTitle.encode('utf-8')))
    if(modifyPage(dst,pageTitle,subs)):
      nbModPage = nbModPage + 1
      
  return nbModPage  
  
def uploadFiles(src, dst, files) :
  """Download files from src site and upload on dst site
    
    return the number of succes uploaded files
  """
  
  nbFiles = len(files)
  for i,fileTitle in enumerate(files):
    try:
      # create a new file on dest wiki
      pageDst = FilePage(dst, fileTitle)
      f = FilePage(src, fileTitle)
      if(not pageDst.exists()):
        print ("%i/%i Upload file %s" % 
          (i+1, nbFiles,  fileTitle.encode('utf-8')))
        sys.stdout.flush()
        # start upload !
        dst.upload( pageDst, source_url=f.get_file_url(), 
                    comment=fileTitle, text=f.text, 
                    ignore_warnings = False)
                    
    except Exception as e:
      print ("Error on upload file %s (%s)" % 
              (fileTitle.encode('utf-8'),e))  

def syncPages(src, dst, pages, force = False) -> int: 
  """Synchronize wiki pages from src to dst
  
    force : if true, always copy  the content (even if page exist on site dest) 
    
    return the number of succes synchronized pages 
  """
  
  nbSyncPage = 0
  nbPage = len(pages)
  
  for i,p in enumerate(pages):
    print ("%i/%i Sync %s " % 
            (i+1,nbPage,p.encode('utf-8')))
    sys.stdout.flush()
    if(syncPage(src,dst,p,force)):
      nbSyncPage = nbSyncPage + 1
      
  return nbSyncPage
  
######################################
# Entry points  
  
def syncPagesWithDependances( siteSrc, siteDst, 
                              pages, options) : 
  """ Get the dependances of pages (templates and files),
      sync all pages and upload files contained in the pages
  
    options : dict from args scripts
    
    return the number of succes synchronized pages and files 
  """
  
  # get options
  force = options['force']
  exportDir = options["exportDir"]
  
  print ("%i pages to sync" % len(pages))
  # export titles of collected pages to sync
  exportPagesTitle(pages,"pages",exportDir)
    
  if(options['templatesSync']):
    # try to restore precedent state
    templates = importPagesTitle("templates",exportDir)
    if(len(templates) > 0 and not force):
      # the imported file contains all templates to sync
      options['templatesDepSync'] = False
    else:
      # collect template used by pages
      templates = getTemplatesFromPages(siteSrc, pages)
      exportPagesTitle(templates,"templates",exportDir)
    print ("%i templates to sync" % len(templates))
    
  #collect files used by pages
  if(options['filesUpload']) :
    # try to restore precedent state
    files = importPagesTitle("files",exportDir)
    if(len(files) == 0 or force):
      files = getFilesFromPages(siteSrc, pages)
      exportPagesTitle(files,"files",exportDir)
    print ("%i files to sync" % len(files))
    
  if(options['templatesDepSync']):    
    dependances = getTemplatesFromPages(siteSrc, templates)
    #delete duplicate
    templates = list(set(templates+dependances))
    exportPagesTitle(templates,"templates",exportDir)
    print ("%i templates to sync" % len(templates))
    
  #sync all pages, templates and associated files
  nbPageSync = 0
  
  print ("====== Sync pages")
  nbPageSync += syncPages(siteSrc, siteDst, pages, force )  
    
  if(options['templatesSync']):
    print ("====== Sync template")
    nbPageSync += syncPages(siteSrc, siteDst, templates, force )
    
  if(options['filesUpload']):
    print ("====== Upload files")
    uploadFiles (siteSrc, siteDst, files)      
  
  return nbPageSync;  
  
def syncAndModifyPages(
  srcFam, srcCode, dstFam, dstCode, 
  pagesName, categories, 
  modifications, options) :
  """Synchronize wiki pages from named page list
        and named categories list
    
    return the number of succes synchronized pages and files
    
  """  
  
  # configure sites
  siteSrc = Site(fam=srcFam,code=srcCode)
  siteDst = Site(fam=dstFam,code=dstCode)
  
  siteDst.login()
  
  #disable slow down wiki write mechanics 
  siteDst.throttle.maxdelay=0  
  
  pages = pagesName
  
  if( categories ):
    cats = [(Category(
                siteSrc,
                c['title']),
                c['namespace'],
                c['recurse']
            ) for c in categories ]
    # retrieve all pages from categories
    for (cat,ns,r) in cats :
      pages.append(cat.title())
      print ("Retrieve pages from " + cat.title())
      # add pages to sync of this categorie
      pages.extend(mapTitle(cat.articles( namespaces=ns, recurse=r )))
    
  # copy all pages !
  nbPages = syncPagesWithDependances(siteSrc, siteDst, pages, options)    
  
  # apply modifications
  nbMods = 0
  if( modifications ):
    for mod in modifications :
      # get all pages to modify from regex mod['pages']
      pageMods = filter( 
               lambda p : re.search(mod['pages'],p ), 
               pages
             )
      
      # get all supstitution to apply on list of pages
      subs = map( 
               lambda s : (re.compile(s['pattern']),s['repl']), 
               mod['substitutions']
             )
      
      # apply set() on pageMods to delete duplicate
      nbMods = modifyPages(siteDst, list(set(pageMods)), list(subs))
      
  
  return (nbPages,nbMods)


def processFromJSONFile(fileconfig, options):
  """Synchronize wiki pages from JSON file
    
    return the number of succes synchronized pages and files
  """
  print ("Process %s" % fileconfig)

  with open(fileconfig, 'r', encoding='utf-8') as jsonfile:
    try:
      cfg = json.load(jsonfile)

      src = cfg['sites']['src']
      dst = cfg['sites']['dst']
      pages = cfg['pages']
      cats = cfg['categories']
      mods = cfg['modifications']
      
      (nbPages,nbMods) = syncAndModifyPages(
        src['fam'], src['code'], 
        dst['fam'], dst['code'], 
        pages, cats, mods, options
      )
      
      print ("%i pages synchronized and %i pages modify" % (nbPages, nbMods))
      
    except json.decoder.JSONDecodeError as e:
      print ("Syntax error in mirroring file : %s" % e)
    except KeyError as e:
      print ("KeyError error in mirroring file : %s" % e)
    except Exception as e:
      print ("Program exit with error : %s" % e)
      

######################################
# Main parts

def main():
  options = DEFAULT_OPTIONS
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], 
      "hftdue:", 
      [ "help",
        "force",
        "no-sync-templates",
        "no-sync-dependances-templates",
        "no-upload-files",
        "export-dir"
      ]
    )
  except (getopt.error, msg):
    print (("args error : %s" % str(msg)))
    print ("Use --help to show help instructions")
    sys.exit(2)

  # parse args
  for (opt, arg) in opts:
    if opt in ("-h", "--help"):
      print(__doc__)
      sys.exit(0)
    if opt in ("-f", "--force"):
      options["force"] = True
    if opt in ("-t", "--no-sync-templates"):
      options["templatesSync"] = False
    if opt in ("-d", "--no-sync-dependances-templates"):
      options["templatesDepSync"] = False
    if opt in ("-u", "--no-upload-files"):  
      options["filesUpload"] = False
    if opt in ("-e", "--export-dir"):  
      options["exportDir"] = arg
            
  # check coherence, fix if needed
  if(options["templatesDepSync"] and not options["templatesSync"]):
      options["templatesSync"] = True

  print (options)

  # process each config file
  for arg in args:
    processFromJSONFile(arg,options)
    
  sys.stdout.flush()
    
if __name__ == "__main__":
  main()

######################################
# Test parts

def test():
  #syncPagesAndCategories("wikipedia","en","kiwix","kiwix",["Redirect_Message"],[],DEFAULT_OPTIONS)
  processFromJSONFile("test.json", DEFAULT_OPTIONS)

