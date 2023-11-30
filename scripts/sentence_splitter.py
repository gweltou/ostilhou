#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from ostilhou.text import split_sentences


if __name__ == "__main__":

    with open(sys.argv[1], 'r') as f_in:
        data = ''.join(f_in.readlines())
    
    parts = data.split('\n\n')
    for part in parts:
        for sentence in split_sentences(part, end=''):
            print(sentence)
        print()