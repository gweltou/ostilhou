#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
    Convert a srt files to split and txt files
"""

import os
import re
import sys


TIMECODE_PATTERN = re.compile(r"(?:(\d+):)?(\d+):(\d+),(\d+) --> (?:(\d+):)?(\d+):(\d+),(\d+)")



def srt2split(lines):
    segments = []
    text = []
    next_is_text = False
    for line in lines:
        line = line.strip()
        if not line:
            next_is_text = False
        elif next_is_text:
            if text[-1] != "":
                text[-1] += ' '
            text[-1] += line
        else:
            match = TIMECODE_PATTERN.match(line)
            if match:
                # print(match.groups())
                h1, m1, s1, ms1, h2, m2, s2, ms2 = match.groups(default=0)
                t1 = int(h1) * 60 * 60_000 + int(m1) * 60_000 + int(s1) * 1000 + int(ms1)
                t2 = int(h2) * 60 * 60_000 + int(m2) * 60_000 + int(s2) * 1000 + int(ms2)
                segments.append((t1, t2))
                text.append('')
                next_is_text = True
    
    return segments, text



if __name__ == "__main__":

    # for filename in os.listdir():
    for filename in sys.argv[1:]:
        basename, ext = os.path.splitext(filename)
        if ext.lower() == ".srt":
            print(filename)
            with open(filename, 'r') as fin:
                segments, text = srt2split(fin.readlines())
            
            with open(basename + ".txt", 'w') as fout:
                fout.writelines([t+'\n' for t in text])

            with open(basename + ".split", 'w') as fout:
                fout.writelines([f"{s[0]} {s[1]}\n" for s in segments])
