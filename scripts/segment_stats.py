#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Displays the distribution of segments's length in a given directory

Usage : ./segment_stats.py aligned_data/

Author:  Gweltaz Duval-Guennoc
"""


import sys
import os
from math import floor, ceil

import matplotlib.pyplot as plt

from ostilhou.asr.dataset import load_ali_file
from ostilhou.utils import sec2hms, list_files_with_extension, read_file_drop_comments


if __name__ == "__main__":
    bins = [0]*16

    aligned_files = list_files_with_extension([".ali", ".seg", ".split"], sys.argv[1])
    for filename in aligned_files:
        if filename.lower().endswith(".ali"):
            segments = load_ali_file(filename)["segments"]
        else:
            segments = [ line.split() for line in read_file_drop_comments(filename) ]
            segments = [ (int(s)/1000, int(e)/1000) for s, e in segments ]

        for i, (s, e) in enumerate(segments):
            dur = e - s
            if dur > 25 or dur < 1.5:
                print(round(dur, 2), filename, i)
            bin_i = min(int(dur/2), len(bins) - 1)
            bins[bin_i] += 1
    
    print(bins)
    print(sum(bins))

    # plt.plot(bins)
    x = [ f"{2*a}-{2*a+2}" for a in range(len(bins)-1)]
    x.append(f"{2*(len(bins)-1)}+")
    plt.bar(x, bins)
    # plt.hist(bins, range(0, 16, 2))
    plt.show()
