#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

"""
 wikimedia_sync.py

 usage : ./wikimedia_sync.py <config_file.py>

 author : Florent Kaisser

 Copy WikiMedia pages from a Wiki source (ex : a Wikipedia) to a Wiki 
 destionation (like a third-party wikis).

 A config file given in args contain name of pages and categories to 
 synchronize, and Wiki source and destination.

 IMPORTANT : We must have user-password.py and user-config.py in same 
 directory of this script to congigure pywikibot. 
 See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
"""

# For use WikiMedia API
from pywikibot import Site,Page,Category,logging

# For load YAML file config
import sys
import yaml

# We use typing 
from typing import List
PageList = List[Page]


def syncPages(src : Site, dst : Site, pages : PageList) -> int: 
  """Synchronize wiki pages from src to dst
    
    return the number of synchronized pages succes
  """
  
  nbSyncPage = 0
  
  #disable mechanics to slow down wiki write
  dst.throttle.maxdelay=0
  
  for p in pages:
    print ("== Sync " + p.title())
    
    # create a new page on dest wiki
    newPage = Page(dst, p.title())
    
    # copy the content of the page
    newPage.text = p.text
    
    # commit the new page on dest wiki
    if (dst.editpage(newPage)):
      nbSyncPage = nbSyncPage + 1
    else:
      print ("Error on saving page")

  return nbSyncPage
  
def syncPagesAndCategories(
  srcFam : str, srcCode : str, dstFam : str, dstCode : str, 
  pagesName : List[str], categoriesName : List[str]) -> int :
  """Synchronize wiki pages from named page list
        and named categories list
    
    return the number of synchronized pages succes
  """  
  
  # configure sites
  siteSrc = Site(fam=srcFam,code=srcCode)
  siteDst = Site(fam=dstFam,code=dstCode)
  
  # pages from their names
  pages = [ Page(siteSrc, name) for name in pagesName ]
  
  # retrieve all pages from categories
  categories = [ Category(siteSrc,name) for name in categoriesName ]
  for cat in categories :
    print ("Retrieve pages from " + cat.title())
    # add pages of this categorie to pages list to sync
    pages += [ p for p in cat.articles() ]
  
  return syncPages(siteSrc, siteDst, pages )

######################################
# Main parts

def main(fileconfig):
  with open(fileconfig, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    src = cfg['sites']['src']
    dst = cfg['sites']['dst']
    pages = cfg['pages']
    cats = cfg['categories']
    
    nb = syncPagesAndCategories(src['fam'], src['code'], dst['fam'], 
      dst['code'], pages, cats)
      
    print ("%i pages synchronized" % nb)

if __name__ == "__main__":
  if(len(sys.argv)>1):
    main(sys.argv[1])
  else:
    print ("Usage : ./wikimedia_sync.py <config_file.py>")
  

######################################
# Test parts

def test() -> bool:
  siteSrc = Site(fam="wikipedia",code="en")
  siteDst = Site(fam="kiwix")
  pages = [Page(siteSrc,"New_York_City"), 
           Page(siteSrc,"Paris"), 
           Page(siteSrc,"Geneva") ]
           
  simpleTest = (syncPages(siteSrc, siteDst, pages) == 3)
  
  pagesName = ["The_Handmaid's_Tale_(TV_series)","Black_Mirror","The_Wire"]
  catsName = ["Cuba","Lille"]
  
  mainTest = ( syncPagesAndCategories("wikipedia","en","kiwix","kiwix",
                pagesName, catsName ) == 27)
  
  return simpleTest and mainTest

#if __name__ == "__main__":
#  if test():
#    print ("Test OK")
#  else:
#    print ("Test Error")
