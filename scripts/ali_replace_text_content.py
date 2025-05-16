#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Usage:
        $ ali_replace_text_content.py file.ali text.txt translated.ali
"""


import sys
from ostilhou.asr.dataset import load_ali_file, create_ali_file


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 ali_replace_text_content.py file.ali text.txt translated.ali")
        sys.exit(1)
    
    with open(sys.argv[2], 'r') as _f:
        tr_lines = _f.readlines()
        tr_lines = [l.strip() for l in tr_lines]
        tr_lines = list(filter(lambda x: x, tr_lines))
    
    ali_data = load_ali_file(sys.argv[1])
    
    m = min(len(tr_lines), len(tr_lines))
    
    tr = list(zip(tr_lines[:m], ali_data["sentences"][:m]))
    
    for i, line in enumerate(tr):
        print(f"{i} {'\t'.join(line)}")
    
    assert len(tr_lines) == len(ali_data["sentences"]), f"Number of sentences doesn't match {len(ali_data["sentences"])} != {len(tr_lines)}"
    
    with open(sys.argv[3], 'w') as _fout:
        _fout.write(
            create_ali_file(
                tr_lines, ali_data["segments"],
                audio_path=ali_data["audio_path"]
            )
        )
