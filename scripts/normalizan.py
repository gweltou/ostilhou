#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import argparse

from ostilhou.text import normalize_sentence


if __name__ == "__main__":
    input = sys.stdin
    output = sys.stdout

    while True:
        data = input.readline()
        if data:
            print(normalize_sentence(data), file=output)