#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: verify_text_file.py

Check spelling for each line in a text file

Usage: ./verify_text_file.py filename.txt

Author: Gweltaz Duval-Guennoc
"""


import sys
import os
import re

from colorama import Style

from ostilhou.text import get_hspell_mistakes
from ostilhou.utils import list_files_with_extension, green
from ostilhou.asr.dataset import parse_ali_file

from ostilhou.text import (
    pre_process, normalize_sentence, filter_out_chars,
    split_sentences, tokenize, detokenize, normalize, TokenType,
    PUNCTUATION,
    VALID_CHARS
)


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as _fin:    
        total_errors = 0
        all_errors = {}

        for i, line in enumerate(_fin.readlines()):
            correction, num_errors, errors = get_hspell_mistakes(line)
            total_errors += num_errors
            if errors:
                # print(f"{Style.DIM}[{text.strip()}]{Style.RESET_ALL}")
                print(f"[{i}] {correction}")
                for err in errors:
                    err = err.lower()
                    if err in all_errors:
                        all_errors[err] += 1
                    else:
                        all_errors[err] = 1
        
    print(f"{total_errors} spelling mistakes")

    top_errors = list(all_errors.items())
    top_errors.sort(key=lambda i: i[1], reverse=True)
    for k, v in top_errors[:50]:
        print(f"{k}\t{v}")
