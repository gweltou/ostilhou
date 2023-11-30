#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command line:
	wget -r -nc -A.html ya.bzh

"""

import os
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import json

import sys
from ostilhou.utils import list_files_with_extension
import re




def parseHTML(htmlfile):
    pattern_niverenn = re.compile(r"embannet en niverenn(?:où)? (\d+)(?:-(\d+))?(?: ha (\d+))?", re.IGNORECASE)

    class MyHTMLParser(HTMLParser):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.in_content = False
            self.in_title = False
            self.in_date = False
            self.in_sup = False # between <sup> and </sup>
            self.capture_data = False
            self.depth = 0
            self.tags = set()
            self.content = ""
            self.title = ""
            self.date = ""
            self.journal_num = []
        
        def handle_starttag(self, tag, attrs):
            if not self.in_date and not self.date and tag == "time":
                self.in_date = True
            
            if not self.in_title and tag == "h1":
                self.in_title = True
		    
            if self.in_content:
                self.tags.add(tag)
                if tag in ("p", "strong", "em", "a", "div", "ul", "li", "sup"):
                    # print(self.depth * " " + f"<{tag}>")
                    self.depth += 1
                    if tag in ("p", "li"):
                        self.capture_data = True
                    elif tag in ("sup"):
                        self.in_sup = True
                elif tag in ("br"):
                    self.content += '\n'
			
            if not self.in_content and tag == "div":
                for key, val in attrs:
                    if key == "class" and "td-post-content" in val.split():
                        self.in_content = True
		
        def handle_endtag(self, tag):
            #self.allow_data = False
            if self.in_title and tag == "h1":
                self.in_title = False
            
            if self.in_date and tag == "time":
                self.in_date = False
            
            if self.in_content and tag in ("p", "strong", "em", "a", "div", "ul", "li", "sup"):
                self.depth -= 1
                if tag in ("p", "li"):
                    self.content += '\n'
                    self.capture_data = False
                elif tag in ("sup"):
                    self.in_sup = False
                # print(self.depth * " " + f"</{tag}>")
            
            if self.in_content and tag == "div" and self.depth == 0:
                self.in_content = False
            
        
        def handle_data(self, data):
            #data = ' '.join(data.split())
            if self.in_title:
                self.title = data
            
            if self.in_date:
                self.date = data
            
            if self.capture_data and data:
                if self.in_sup and data.isdigit():
                    # Marks a footnote, we skip it
                    return
                
                self.content += data
                match = re.search(pattern_niverenn, data)
                if match:
                    self.journal_num.extend(filter(None, match.groups()))
	
    parser = MyHTMLParser()
    
    with open(htmlfile, 'r') as f:
        parser.feed(f.read())

    return {"title" : parser.title, "date" : parser.date, "num": parser.journal_num, "text" : parser.content}



"""
def parseXML(xmlfile):

	# create element tree object
	tree = ET.parse(xmlfile)

	# get root element
	root = tree.getroot()

	# create empty list for news items
	newsitems = []

	# iterate news items
	#for item in root.findall('./channel/item'):
	for item in root.findall('div'):
		print(item)
		# empty news dictionary
		news = {}
		# iterate child elements of item
		for child in item:
			# special checking for namespace object content:media
			if child.tag == '{http://search.yahoo.com/mrss/}content':
				news['media'] = child.attrib['url']
			else:
				news[child.tag] = child.text.encode('utf8')
		# append news dictionary to news items list
		newsitems.append(news)
	
	# return news items list
	return newsitems
"""



if __name__ == "__main__":
    html_files = list_files_with_extension(".html", "ya.bzh")
    
    # Remove feed pages
    html_files = [fname for fname in html_files if "feed" not in fname]
    # Remove tag pages
    html_files = [fname for fname in html_files if "/tag/" not in fname]
    # Remove files in download pages
    html_files = [fname for fname in html_files if "/download/" not in fname]
    # Remove files in category pages
    html_files = [fname for fname in html_files if "/category/" not in fname]
    html_files = [fname for fname in html_files if "/author/" not in fname]
    html_files = [fname for fname in html_files if "/wp-json/" not in fname]

    blacklisted = [
        "ya.bzh/pellgargan-ar-ya-niverel/index.html",
        "ya.bzh/enrolladennou/index.html",
        "ya.bzh/menegou-lezennel/index.html",
        "ya.bzh/steunvenn-al-lechienn/index.html",
        "ya.bzh/koumanantin/index.html",
        "ya.bzh/piv-omp/index.html"]

    html_files = [fname for fname in html_files if fname not in blacklisted]
    
    with open("ya_dump.txt", 'w') as fout:
        for f in html_files:
            print(f)
            article = parseHTML(f)
            print("Titre:", article["title"])
            print("Date:", article["date"])
            print("Num:", ', '.join(article["num"]))
            print()
            fout.write(article["text"])
    
    print(f"{len(html_files)} articles saved")
