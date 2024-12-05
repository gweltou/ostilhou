#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Prints the textual content of an ALI file to stdout
    
    Usage:
        $ ali_print_text.py file.ali
"""


import sys
import re
from ostilhou.asr.dataset import load_ali_file


if __name__ == "__main__":
    ali_data = load_ali_file(sys.argv[1])

    for line in ali_data["sentences"]:
        line = re.sub(r"<br>", '\u2028', line, flags=re.IGNORECASE)
        line = re.sub(r"</?([a-zA-Z \']+)>", '', line)
        print(line)
