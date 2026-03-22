#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import srt
import os
import argparse
from datetime import timedelta

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("srtfile", help="SubRip subtitle file")
    parser.add_argument("--add", help="Offset in seconds. Provide 1 value (for both) or 2 space-separated values (for start and end)", type=float, nargs='+', default=[0.0])
    parser.add_argument("--mul", help="Change fps of subtitles (ex: 25/29.97)", type=str, default="1.0")
    parser.add_argument("-o", "--output", help="Path to the converted file")
    args = parser.parse_args()
    
    # Process division in mul argument
    if '/' in args.mul:
        num, den = args.mul.split('/')
        args.mul = float(num) / float(den)
    else:
        args.mul = float(args.mul)
    
    if args.output == None:
        dirs, filename = os.path.split(args.srtfile)
        basename, ext = os.path.splitext(filename)
        new_path = os.path.join(dirs, basename + "_conv" + ext)
        args.output = new_path
    
    add_start = args.add[0]
    add_end = args.add[1] if len(args.add) > 1 else args.add[0]
    
    new_subs = []
    with open(args.srtfile, 'r') as _fin:
        for sub in srt.parse(_fin.read()):
            start_s = sub.start.total_seconds() * args.mul + add_start
            end_s = sub.end.total_seconds() * args.mul + add_end
            assert start_s < end_s
            
            sub.start = timedelta(seconds=start_s)
            sub.end = timedelta(seconds=end_s)
            new_subs.append(sub)
            
    with open(args.output, 'w') as _fout:
        _fout.write(srt.compose(new_subs))
