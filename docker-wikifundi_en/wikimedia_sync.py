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
  -u", --no-upload-files : do not copy files (images, css, js, sounds, ...) used by the pages to sync. Default : False
  
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
      "Categorie 1",
      "Catgegorie 2"
      ...
    ]

  }

 IMPORTANT : We must have user-password.py and user-config.py in same 
 directory of this script to congigure pywikibot. 
 See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
"""

#TODO add logging

# For use WikiMedia API
from pywikibot import Site,Page,FilePage,Category,logging

# For load JSON file config and check options
import sys
import json
import getopt

# To use regular expression
import re



DEFAULT_OPTIONS = dict(
    force = False, 
    templatesSync = True, 
    templatesDepSync = True, 
    filesUpload = True)
    
def modifyPage(dst, p, subs)  :

  
  try:
  
    for s in subs :
      pattern = s[0]
      repl = s[1]
      p.text = re.sub(pattern, repl, p.text)
    print ("edit " + p.title())
    return dst.editpage(p)
    
  except Exception as e:
      print ("Error to modify page %s (%s)" % (p.title(), e))
      return False 
      
def modifyPages(dst, pages, subs) :  
  nbModPage = 0
  nbPage = len(pages)
  
  for i,p in enumerate(pages):
    print ("== %i/%i Modification of %s " % (i+1,nbPage,p.title()))
    if(modifyPage(dst,p,subs)):
      nbModPage = nbModPage + 1
      
  return nbModPage

def syncPage(src, dst, p, force = False, checkRedirect = True):
  """Synchronize ONE wiki pages from src to dst
  
     return true if success
  """

  # create a new page on dest wiki
  newPage = Page(dst, p.title())
  
  try:      
    # if page exist on dest and no force -> do not sync this page
    if((not force) and newPage.exists()):  
      return False
      
    # sometime, pywikibot return a page in a different site, 
    # here check this
    elif(newPage.site == dst):
    
      #sync also the redirect target 
      if(p.isRedirectPage()):
        syncPage(src, dst, p.getRedirectTarget(), force, False)
        
      # copy the content of the page
      newPage.text = p.text
      
      # commit the new page on dest wiki
      return dst.editpage(newPage)
      
  except Exception as e:
    print ("Error on sync page %s (%s)" % (p.title(), e))
    return False
    
  return False
  
def uploadFiles(src, dst, files) :
  """Download files from src site and upload on dst site
    
    return the number of succes uploaded files
  """
  
  nbImages = len(files)
  for i,f in enumerate(files):
    try:
      # create a new file on dest wiki
      pageDst = FilePage(dst, f.title())
      if(not pageDst.exists()):
        print ("== %i/%i Upload file %s" % (i+1, nbImages,  f.title()))
        # start upload !
        dst.upload( pageDst, source_url=f.get_file_url(), 
                    comment=f.title(), text=f.text, 
                    ignore_warnings = False)
                    
    except Exception as e:
      print ("Error on upload file %s (%s)" % (f.title(),e))  

def syncPages(src, dst, pages, force = False) -> int: 
  """Synchronize wiki pages from src to dst
  
    force : if true, always copy  the content (even if page exist on site dest) 
    
    return the number of succes synchronized pages 
  """
  
  nbSyncPage = 0
  nbPage = len(pages)
  
  for i,p in enumerate(pages):
    print ("== %i/%i Sync %s " % (i+1,nbPage,p.title()))
    if(syncPage(src,dst,p,force)):
      nbSyncPage = nbSyncPage + 1
      
  return nbSyncPage
  
def getTemplatesFromPages(pages) :
  templates = []
  for p in pages :
    # get templates used by p
    tplt = p.templates()
    nbTplt = len(tplt)
    if(nbTplt > 0):
      print ("Process %i templates of %s" % (nbTplt, p.title()))
      templates += tplt
      
  # apply set() to delete duplicate
  return list(set(templates))  
  
def getFilesFromPages(pages) :
  files = []
  for p in pages :
    # get files used by p
    f = list(p.imagelinks())
    nbFiles = len(f)
    if(nbFiles > 0):
      print ("Process %i images of %s" % (nbFiles, p.title()))
      files += f  
      
  # apply set() to delete duplicate
  return list(set(files))
  
def syncPagesWithDependances( siteSrc, siteDst, 
                              pages, options) : 
  """ Get the dependances of pages (templates and files),
      sync all pages and upload files contained in the pages
  
    options : dict from args scripts
    
    return the number of succes synchronized pages and files 
  """

  #get templates and files used by pages
  
  if(options['filesUpload']) :
    images = getFilesFromPages(pages)
    
  if(options['templatesSync']):
    templates = getTemplatesFromPages(pages)
    
  if(options['templatesDepSync']):    
    dependances = getTemplatesFromPages(templates)
  
  #sync all pages, templates and associated files
  nbPageSync = 0
  
  if(options['templatesDepSync']):
    print ("====== Sync template dependances")
    nbPageSync += syncPages(siteSrc, siteDst, dependances, options['force'] )
    
  if(options['templatesSync']):
    print ("====== Sync template")
    nbPageSync += syncPages(siteSrc, siteDst, templates, options['force'] )
    
  print ("====== Sync pages")
  nbPageSync += syncPages(siteSrc, siteDst, pages, options['force'] )  
  
  if(options['filesUpload']):
    print ("====== Upload files")
    uploadFiles (siteSrc, siteDst, images)  
  
  return nbPageSync;  
  
#############
  
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
  
  pages = []
  
  if( pagesName ):
    # pages from their names
    pages += [ Page(siteSrc, name) for name in pagesName ]
  
  if( categories ):
    cats = [(Category(
                siteSrc,
                c['title']),
                c['namespace'],
                c['recurse']
            ) for c in categories ]
    # retrieve all pages from categories
    for (cat,ns,r) in cats :
      pages += [ Page(siteSrc, cat.title()) ]
      print ("Retrieve pages from " + cat.title())
      # add pages to sync of this categorie 
      pages += list( cat.articles( namespaces=ns, recurse=r ) )
    
  # copy all pages !
  nbPages = syncPagesWithDependances(siteSrc, siteDst, pages, options)    
  
  # apply modifications
  nbMods = 0
  if( modifications ):
    for mod in modifications :
      # get all pages to modify from regex mod['pages']
      pageModsOnSrc = filter( 
               lambda p : re.search(mod['pages'],p.title()), 
               pages
             )
      # We must modify on dest site, 
      # then get pages to modify on this site
      pageMods = map(
               lambda p : Page(siteDst, p.title()),
               pageModsOnSrc
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

  with open(fileconfig, 'r') as jsonfile:
    cfg = json.load(jsonfile)
    
    # TODO add Exceptions
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
    #TODO end exception
      
    print ("%i pages synchronized and %i pages modify" % (nbPages, nbMods))

######################################
# Main parts

def main():
  options = DEFAULT_OPTIONS
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], 
      "hftdu", 
      [ "help",
        "force",
        "no-sync-templates",
        "no-sync-dependances-templates",
        "no-upload-files"
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
      
  # check coherence, fix if needed
  if(options["templatesDepSync"] and not options["templatesSync"]):
      options["templatesSync"] = True

  # process each config file
  for arg in args:
    processFromJSONFile(arg,options)
    
if __name__ == "__main__":
  main()

######################################
# Test parts

def test():
  #syncPagesAndCategories("wikipedia","en","kiwix","kiwix",["Redirect_Message"],[],DEFAULT_OPTIONS)
  processFromJSONFile("test.json", DEFAULT_OPTIONS)

