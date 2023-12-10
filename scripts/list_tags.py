#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path

from ostilhou.utils import list_files_with_extension
from ostilhou.asr.dataset import get_text_header


if __name__ == "__main__":
	
	seg_files = list_files_with_extension((".split", ".seg"), sys.argv[1])
	seg_files.sort()
	all_tags = set()
	tag = None if len(sys.argv) <= 2 else sys.argv[2]
	
	for sf in seg_files:
		seg_ext = os.path.splitext(sf)[1]
		text_file = sf.replace(seg_ext, ".txt")
		if not os.path.exists(text_file):
			print("No text file for", sf)
			continue
		
		metadata = get_text_header(text_file)
		if "tags" in metadata:
			if tag:
				if tag in metadata["tags"]:
					print(os.path.abspath(sf))
			else:
				print(text_file)
				print(metadata["tags"])
			all_tags.update(metadata["tags"])
	
	if not tag:
		print(all_tags)
