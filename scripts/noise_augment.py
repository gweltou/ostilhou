#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
from os import makedirs
import shutil
import argparse

from ostilhou.utils import list_files_with_extension
from ostilhou.audio import add_whitenoise
from ostilhou.asr import load_text_data, load_ali_file


"""
Data Augmentation by adding noise to audiofiles

Usage:
    python3 noise_augment.py file_list.txt

"""


EXCLUDE_FROM_LM = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filelist", help="List of files to be augmented, in text format")
    parser.add_argument("-o", "--output", help="Path where to write the augmented files",
                        default=os.path.join(os.getcwd(), "augmented"))
    args = parser.parse_args()

    assert os.path.exists(args.filelist)

    with open(args.filelist, 'r', encoding='utf-8') as f:
        files = [ filename.strip() for filename in f if filename.strip() ]


    for filepath in files:
        filename = os.path.split(filepath)[1]
        file_ext = os.path.splitext(filename)[1]

        if file_ext.lower() == ".ali":
            ali_data = load_ali_file(filepath)
            soundfile = ali_data["audio_path"]
        else:
            soundfile = filepath.replace(file_ext, ".wav")
        
        dest = os.path.join(args.output, filename)
        soundfile_dest = os.path.join(args.output, os.path.split(soundfile)[1])
        if not soundfile_dest.lower().endswith(".wav"):
            soundfile_dest = soundfile_dest[:-4] + ".wav"

        if not os.path.exists(dest):
            makedirs(args.output, exist_ok=True)
            
            add_whitenoise(soundfile, soundfile_dest, -22)
            
            # Copy split and text files
            shutil.copy(filepath, dest)

            if file_ext.lower() == ".ali":
                continue
            
            txt_file = filepath.replace(file_ext, ".txt")
            if EXCLUDE_FROM_LM:
                data = load_text_data(txt_file)
                with open(dest.replace(file_ext, ".txt"), 'w', encoding='utf-8') as fout:
                    fout.write("{parser: no-lm}\n\n")
                    for line in data:
                        fout.write(f"{line[0]}\n")
            else:
                shutil.copy(txt_file, dest.replace(file_ext, ".txt"))
