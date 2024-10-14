#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script used to build a quintessentially distilled corpus from a wikipedia dump.

Usage:
    python mcv_wikipedia_cleaner.py wiki_dump.txt > distilled.txt
"""



import sys
from hashlib import md5
from ostilhou.text import (
    strip_punct, PUNCTUATION, 
)
from ostilhou.dicts import acronyms
from ostilhou.text.definitions import (
    is_unit_number, is_roman_number, is_ordinal, is_roman_ordinal, is_word,
)


def tokenize(word: str) -> str:
    if word.isdecimal():
        if len(word) > 4:
            return "<BIG_NUM>"
        else:
            return "<NUM>"
    return word

def get_tokens(sentence: str) -> str:
    words = sentence.split()
    words = [w for w in map(strip_punct, words) if w]
    words = list(map(tokenize, words))
    return words


with open(sys.argv[1], 'r') as fin:
    lines = fin.readlines()

seen = set()
cleaned = set()

first_words = dict()

for line in lines:
    line = line.strip()
    if not line:
        continue

    if line.startswith(',') or line.startswith(';'): continue
    if '(' in line or ')' in line: continue
    if '/' in line: continue
    if ':' in line: continue
    if ',,' in line: continue
    if ',.' in line: continue
    if line.count(';') > 1: continue
    if 'WWW' in line: continue
    if "Saint" in line: continue
    if "kent J" in line: continue
    if "a-raok J" in line: continue
    if "goude J" in line: continue
    if "pennad-" in line: continue
    if ", ed." in line: continue
    #if "niv." in line.lower(): continue
    if "Al Liamm" in line: continue
    if line.startswith("Ur pennad"): continue
    if line.startswith("Lec'hienn ofisiel"): continue
    if line[-1] not in ".!?…;": continue

    
    tokens = get_tokens(line)
    if len(tokens) > 15: continue
    if len(tokens) < 3: continue
    
    if not is_word(tokens[0]): continue
    elif tokens[0][0].islower(): continue
        
    if tokens[0] == "<NUM>": continue
    if tokens[-1] == "<NUM>" or tokens[-1] == "<BIG_NUM>": continue
    if "<BIG_NUM>" in tokens: continue
    if tokens.count("<NUM>") > 1: continue
    if "SUA" in tokens: continue
    if "the" in tokens or "The" in tokens: continue
    if tokens[0] == "Iliz": continue
    if tokens[0] == "Chapel": continue
    if tokens[0] == "San": continue
    if "st" in tokens or "St" in tokens: continue
    if "KJK" in tokens: continue
    if "EBSSA" in tokens: continue
    if "Kensonenn" in tokens: continue
    if tokens[0] in ("Gwelet", "Gwelit", "Gwelout"): continue
    if len(tokens[0]) > 1 and tokens[0].isupper() and not "'" in tokens[0]: continue

    if any(map(is_unit_number, tokens)): continue
    if any(map(is_roman_number, tokens)): continue
    if any(map(is_ordinal, tokens)): continue
    if any(map(is_roman_ordinal, tokens)): continue
    if any(map(lambda w: w.upper() in list("BCDFGHIJKLMNPQRSTUVWXYZ"), tokens)): continue
    if any(map(lambda w: '-' not in w and len(w.lower().replace("c'h", '_')) > 15, tokens)):
        continue
    if any(map(lambda w: len(w) > 2 and is_word(w) and w.isupper() and not w in acronyms, tokens)):
        continue

    head_tokens = ' '.join(tokens[:3]).lower()
    hash = md5(head_tokens.encode("utf-8")).hexdigest()
    if hash in seen: continue
    
    seen.add(hash)
    cleaned.add(line + '\n')


for line in sorted(cleaned):
    print(line)

print(len(cleaned), file=sys.stderr)
