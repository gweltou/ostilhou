#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
    File: srt2seg.py

    Converts a srt or vtt file to a seg (audio segments timecodes) and a txt file.
    The resulting files will be created in the same folder as the source srt/vtt file.

    Usage:
        python3 srt2seg.py subtitles.srt
    
    Author: Gweltaz Duval-Guennoc (2023)
"""

import os
import re
import sys


TIMECODE_PATTERN = re.compile(r"(?:(\d+):)?(\d+):(\d+)(?:,|.)(\d+) --> (?:(\d+):)?(\d+):(\d+)(?:,|.)(\d+)")


def parse_lines(lines):
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
    
    # Remove formatting escaped tags from text (ex: <i>, </i>)
    text = [ re.sub(r"&lt;/?[a-zA-Z]+&gt;", "", line) for line in text ]
    # Remove escaped non-breakable spaces
    text = [ line.replace("&nbsp;", '') for line in text ]
 
    return segments, text


def srt2segments(*filenames):
	# for filename in os.listdir():
    for filename in filenames:
        basename, ext = os.path.splitext(filename)
        if ext.lower() in (".srt", ".vtt"):
            print(filename)
            with open(filename, 'r') as fin:
                segments, text = parse_lines(fin.readlines())
            
            with open(basename + ".txt", 'w') as fout:
                fout.write("{source: }\n{source-audio: }\n{author: }\n{licence: }\n{tags: }\n\n\n\n\n\n")
                fout.writelines([t+'\n' for t in text])

            with open(basename + ".seg", 'w') as fout:
                fout.writelines([f"{s[0]} {s[1]}\n" for s in segments])


if __name__ == "__main__":
	srt2segments(*sys.argv[1:])
