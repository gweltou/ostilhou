#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Find most common ngrams in a text corpus
Print list of ngrams to stdout in reverse order of number of occurence
"""

import sys
import argparse
from ostilhou.text import (
    strip_punct, PUNCTUATION, 
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


def get_args():
    parser = argparse.ArgumentParser(description="Find common n-grams in text corpus")
    parser.add_argument("filename", help="Text corpus", metavar="FILE")
    parser.add_argument("-n", "--gram", type=int, default=2, metavar="N", help="Size of N-gram")
    parser.add_argument("-l", "--lower", action="store_true", help="Case insensitive")
    parser.add_argument("--head", action="store_true", help="Check only the first n-gram of each line")
    parser.add_argument("-m", "--min", type=int, default=1, metavar="N", help="Should have at least N occurences")
    return parser.parse_args()



if __name__ == "__main__":
    args = get_args()
    
    with open(sys.argv[1], 'r', encoding='utf-8') as _fin:
        lines = _fin.readlines()

    ngrams = dict()

    for line in lines:
        tokens = get_tokens(line)
        
        if len(tokens) < args.gram:
            continue
        if args.lower:
            tokens = [t.lower() for t in tokens]
        
        for i in range(0, len(tokens)-args.gram):
            tg = tuple(tokens[i:i+args.gram])
            
            if tg in ngrams:
                ngrams[tg] += 1
            else:
                ngrams[tg] = 1
            
            if args.head:
                break

    for tg in sorted(ngrams, key=lambda k: ngrams[k]):
        if ngrams[tg] < args.min:
            continue
        print(tg, ngrams[tg])
