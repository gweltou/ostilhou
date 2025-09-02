#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: verify_text_files.py

Check spelling in every ALI file in folder and subfolders
###Prompt for new found acronyms

Usage: ./verify_text_files.py DIRECTORY

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
    ali_files = list_files_with_extension("ali", sys.argv[1])
    
    num_errors = 0
    for file in ali_files:
        if not os.path.exists(file):
            continue

        utterances = parse_ali_file(
            file,
            init={"lang": "br"},
            filter={"lang": "br", "parser": True}
        )

        print(green('* ' + file))

        for i, (regions, segment) in enumerate(utterances):
            text = ''.join([ r["text"] for r in regions ])
            text = text.replace('<br>', ' ')
            text = re.sub(r"\</?[ib]\>", '', text).strip()
            text = text.replace('{?}', '')

            text = pre_process(text)

            correction, errors = get_hspell_mistakes(text)
            num_errors += errors
            if errors:
                # print(f"{Style.DIM}[{text.strip()}]{Style.RESET_ALL}")
                print(f"[{i}] {correction}")
        
            # extract acronyms
            # extracted_acronyms = libMySTT.extract_acronyms_from_file(file)
            # if extracted_acronyms:
            #     with open(libMySTT.ACRONYM_PATH, 'a', encoding='utf-8') as f:
            #         for acr in extracted_acronyms:
            #             f.write(f"{acr} {extracted_acronyms[acr]}\n")
            #             libMySTT.acronyms[acr] = extracted_acronyms[acr]
            #             num_errors -= 1
    
    print(f"{num_errors} spelling mistakes")
