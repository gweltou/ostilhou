#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Prints a list of aligned data files, given a tag

    usage:
        python3 list_tags.py data_folder
        
        python3 list_tags.py data_folder tag
"""


import sys
import os.path

from colorama import Fore

from ostilhou.utils import list_files_with_extension, yellow
from ostilhou.asr.dataset import get_text_header, load_ali_file



if __name__ == "__main__":
    seg_files = list_files_with_extension((".split", ".seg", ".ali"), sys.argv[1])
    seg_files.sort()
    all_tags = set()
    tag = None if len(sys.argv) <= 2 else sys.argv[2]
    
    for sf in seg_files:
        seg_ext = os.path.splitext(sf)[1].lower()
        file_tags = []
        if seg_ext == ".ali":
            metadata = load_ali_file(sf)["header"]
            if "tags" in metadata:
                file_tags = metadata["tags"]
        else:
            text_file = sf.replace(seg_ext, ".txt")
            if not os.path.exists(text_file):
                print("No text file for", sf)
                continue
            
            metadata = get_text_header(text_file)
            if "tags" in metadata:
                file_tags = metadata["tags"]
        all_tags.update(file_tags)

        if tag:
            if tag in file_tags:
                print(os.path.abspath(sf))
        else:
            print(yellow(sf))
            print(file_tags)
    
    
    if not tag:
        print(all_tags)
