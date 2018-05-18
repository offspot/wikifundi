#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
#
# wikimedia_sync.py
#
# usage : ./wikimedia_sync.py <config_file.py>
#
# author : Florent Kaisser
#
# Copy WikiMedia pages from a Wiki source (ex : a Wikipedia) to a Wiki 
# destionation (like a third-party wikis).
#
# A config file given in args contain name of pages and categories to 
# synchronize, and Wiki source and destination.
#
# IMPORTANT : We must have user-password.py and user-config.py in same 
# directory of this script to congigure pywikibot. 
# See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
#

# To use WikiMedia API
from pywikibot import Site,Page,Category,logging

# Typing 
from typing import List
PageList = List[Page]

def syncPages(src : Site, dst : Site, pages : PageList) -> int: 
  nbSyncPage = 0
  
  for p in pages:
    print ("== Sync " + p.title())
    
    # create a new page on dest wiki
    newPage = Page(dst, p.title())
    
    # copy the content of the page
    newPage.text = p.text
    
    # commit the new page on dest wiki
    #if (dst.editpage(newPage)):
    if (dst.editpage(newPage)):
      nbSyncPage = nbSyncPage + 1
    else:
      print ("Error on saving page")

  
  return nbSyncPage

def test() -> bool:
  siteSrc = Site(fam="wikipedia",code="en")
  siteDst = Site(fam="kiwix")
  pages = [Page(siteSrc,"New_York_City"), 
           Page(siteSrc,"Paris"), 
           Page(siteSrc,"Geneva") ]
           
  return (syncPages(siteSrc, siteDst, pages) == 3)
  

if __name__ == "__main__":
  if test():
    print ("Test OK")
  else:
    print ("Test Error")
