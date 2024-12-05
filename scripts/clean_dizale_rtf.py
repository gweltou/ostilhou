#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as fin:
        lines = [l for l in fin.readlines() if l.strip()]
    
    lines = [l.split('\t') for l in lines]
    lines = [t for t in lines if len(t) > 1]    # Remove non utterances
    lines = [(spk, re.sub(r"\(.+?\)", '\n', utt)) for spk, utt in lines]  # Remove interjections
    lines = [(spk, utt) for spk, utt in lines if utt.strip()] # Remove empty utterances

    #lines = [f"{spk}\t{' '.join(utt.split())}\n" for spk, utt in lines]
    new_lines = []
    for _, utt in lines:
        new_lines.extend(utt.split('\n'))
    lines = new_lines
        
    lines = [utt.strip() for utt in lines]
    lines = [f"{' '.join(utt.split())}\n" for utt in lines if utt]

    with open(sys.argv[2], 'w') as fout:
        fout.writelines(lines)
