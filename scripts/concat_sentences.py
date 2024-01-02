#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""


"""

import sys
import os.path



if __name__ == "__main__":

	lines = []
	concat = ""
	
	with open(sys.argv[1], 'r') as f_in:
		for l in f_in.readlines():
			l = l.strip()
			if not l:
				if concat: lines.append(concat)
				concat = ""
			elif l.isupper():	# All caps sentences are put on their own line
				if concat: lines.append(concat)
				lines.append(l)
			elif l[-1] in ".?!": # End of sentence
				lines.append(concat + ' ' + l)
				concat = ""
			else:
				concat = concat + ' ' + l if concat else l
	
	basename, ext = os.path.splitext(sys.argv[1])
	output_path = basename + "_fullsentences" + ext
	with open(output_path, 'w') as f_out:
		for line in lines:
			f_out.write(line.strip() + '\n')
