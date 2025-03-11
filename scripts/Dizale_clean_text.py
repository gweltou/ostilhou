#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:
    $ python3 clean_rtf.py infile.txt > outfile.txt
"""

import sys
import re

from ostilhou.text import (
    filter_out_chars,
    normalize_sentence,
    PUNCTUATION,
)


INCLUDE_SPEAKER_NAMES = False
IGNORE_SPEAKERS = ["NAD"]
IGNORE_WORDS = [
    "aaa", "aaah", "argh",
    "huu",
    "hañ", "mhañ",
    "mm", "mh", "mmm", "mmr", "mmrr", "mff",
    "oo", "ooo", "oooh",
    "rhh", "rha", "rhaa",
    "c'heum",
]
REPLACE_WORDS = [
    ("'meus", "'m eus"),
    ("'neus", "'n eus"),
    ("'moa", "'m oa"),
    ("'noa", "'n oa"),
] # TODO


def is_keeper(sentence:str) -> bool:
    sentence = sentence.lower()
    sentence = filter_out_chars(sentence, PUNCTUATION)
    words = sentence.split()
    words = list(filter(lambda e: e not in IGNORE_WORDS, words))
    if words:
        return True
    return False


def replace_words(sentence:str) -> str:
    words = sentence.split()
    for pattern, sub in REPLACE_WORDS:
        for i, w in enumerate(words):
            if pattern in w:
                words[i] = w.replace(pattern, sub)
    return ' '.join(words)


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as fin:
        lines = [l for l in fin.readlines() if l.strip()]
    
    lines = [l.split('\t') for l in lines]
    lines = [t for t in lines if len(t) > 1]    # Remove non utterances
    lines = [(spk, re.sub(r"\(.+?\)", '\n', utt)) for spk, utt in lines]  # Remove interjections
    lines = [(spk, utt) for spk, utt in lines if utt.strip()] # Remove empty utterances

    new_lines = []
    for spk, utt in lines:
        if spk in IGNORE_SPEAKERS:
            continue
        # Split sentences at interjections
        splitted_line = [s.strip() for s in utt.split('\n') if s.strip()]
        splitted_line = [
            normalize_sentence(s, norm_punct=True, norm_digits=False)
            for s in splitted_line if is_keeper(s)
        ]
        
        # Replace words
        splitted_line = [replace_words(s) for s in splitted_line]

        if not splitted_line:
            continue
        
        if INCLUDE_SPEAKER_NAMES:
            splitted_line[0] = f"{{spk: {spk}}}\t{splitted_line[0]}"
        new_lines.append(splitted_line)
    lines = new_lines
    
    #lines = [f"{' '.join(l)}\nFR:\t\n" for l in lines if l]
    lines = [f"{' '.join(l)}" for l in lines if l]


    for l in lines:
        print(l)
