#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
from os import makedirs
import shutil
import argparse

from ostilhou.utils import list_files_with_extension
from ostilhou.audio import add_whitenoise
from ostilhou.asr import load_text_data


"""
Data Augmentation by adding noise to audiofiles

Usage:
    python3 noise_augment.py file_list.txt

"""


DEST = "augmented"

EXCLUDE_FROM_LM = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filelist", help="List of files to be augmented, in text format")
    parser.add_argument("-o", "--output", help="Path where to write the augmented files",
                        default=os.path.join(os.getcwd(), "augmented"))
    args = parser.parse_args()

    assert os.path.exists(args.filelist)

    with open(args.filelist, 'r') as f:
        seg_files = [ filename.strip() for filename in f if filename.strip() ]


    for file in seg_files:
        seg_filename = os.path.split(file)[1]
        seg_ext = os.path.splitext(seg_filename)[1]
        dest = os.path.join(args.output, seg_filename)
        if not os.path.exists(dest):
            if not os.path.exists(os.path.split(dest)[0]):
                makedirs(os.path.split(dest)[0])
            wav_file = file.replace(seg_ext, ".wav")
            add_whitenoise(wav_file, dest.replace(seg_ext, ".wav"), -22)
            
            # Copy split and text files
            shutil.copy(file, dest)
            
            txt_file = file.replace(seg_ext, ".txt")
            if EXCLUDE_FROM_LM:
                data = load_text_data(txt_file)
                with open(dest.replace(seg_ext, ".txt"), 'w') as fout:
                    fout.write("{parser: no-lm}\n\n")
                    for line in data:
                        fout.write(f"{line[0]}\n")
            else:
                shutil.copy(txt_file, dest.replace(seg_ext, ".txt"))
