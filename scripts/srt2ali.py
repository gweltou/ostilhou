#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
    File: srt2seg.py

    Converts a SRT or VTT file to an ALI file.
    The resulting files will be created in the same folder as the source SRT/VTT file.

    Usage:
        python3 srt2ali.py subtitles.srt
    
    Author: Gweltaz Duval-Guennoc (2023)
"""

import os
import re
import sys

from ostilhou.asr.dataset import format_timecode



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
                t1 = int(h1) * 60 * 60 + int(m1) * 60 + int(s1) + int(ms1) / 1000
                t2 = int(h2) * 60 * 60 + int(m2) * 60 + int(s2) + int(ms2) / 1000
                segments.append((t1, t2))
                text.append('')
                next_is_text = True
    
    # Remove formatting escaped tags from text (ex: <i>, </i>)
    text = [ re.sub(r"&lt;/?[a-zA-Z]+&gt;", "", line) for line in text ]
    # Remove escaped non-breakable spaces
    text = [ line.replace("&nbsp;", '') for line in text ]
 
    return segments, text



def srt2ali(*filenames):
	# for filename in os.listdir():
    for filename in filenames:
        basename, ext = os.path.splitext(filename)
        if ext.lower() in (".srt", ".vtt"):
            with open(filename, 'r', encoding='utf-8') as fin:
                # Segments is in milliseconds
                segments, text = parse_lines(fin.readlines())
            
            with open(basename + ".ali", 'w', encoding='utf-8') as fout:
                fout.write("{tags: subtitles}\n\n")

                for segment, text in zip(segments, text):
                    timecode = f"{{start: {format_timecode(segment[0])}; end: {format_timecode(segment[1])}}}"
                    fout.write(f"{text} {timecode}\n")


if __name__ == "__main__":
	srt2ali(*sys.argv[1:])
