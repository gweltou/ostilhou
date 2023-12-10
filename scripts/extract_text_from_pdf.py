#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import PyPDF2
import sys


if __name__ == "__main__":
    # creating a pdf file object 
    pdfFileObj = open(sys.argv[1], 'rb')
        
    # creating a pdf reader object 
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
        
    # printing number of pages in pdf file 
    n_pages = pdfReader.numPages
        
    # creating a page object 
    for i in range(pdfReader.numPages):
        pageObj = pdfReader.getPage(i) 
        t = pageObj.extractText()
        t = t.replace("™", "'")
        print(t)

    pdfFileObj.close() 
