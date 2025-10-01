#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Print the textual content of an ALI file to stdout.

Usage:
    $ ali_print_text.py file.ali
"""


import sys
import re
from ostilhou.asr.dataset import load_ali_file


if __name__ == "__main__":
    ali_data = load_ali_file(sys.argv[1])

    for line in ali_data["sentences"]:
        #line = re.sub(r"<br>", '\u2028', line, flags=re.IGNORECASE)
        line = re.sub(r"<br>", ' ', line, flags=re.IGNORECASE)
        line = re.sub('\u2028', ' ', line, flags=re.IGNORECASE)
        #line = re.sub(r"</?([a-zA-Z']+)>", '', line)
        for match in re.findall(r"<[a-zA-Z']+>", line, flags=re.IGNORECASE):
            if match.lower() not in ("<i>", "<b>"):
                print(match, file=sys.stderr)
                line = line.replace(match, '')
        
        if '<i>' in line.lower() or '</i>' in line.lower():
            assert line.count("<i>") == line.count("</i>"), line
        print(line)
