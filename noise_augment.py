#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
from os import makedirs
import shutil

from ostilhou.utils import list_files_with_extension
from ostilhou.audio import add_whitenoise
from ostilhou.asr import load_text_data


FOLDER = [
    "#brezhoneg",
    "to_augment",
    ]
DEST = "augmented"

EXCLUDE_FROM_LM = True


if __name__ == "__main__":

    for folder in FOLDER:
        files = list_files_with_extension('.split', os.path.join(sys.argv[1], folder))
        for file in files:
            components = file.split(os.path.sep)
            dest = os.path.join( *([DEST] + components[1:]) )
            print(dest)
            if not os.path.exists(dest):
                if not os.path.exists(os.path.split(dest)[0]):
                    makedirs(os.path.split(dest)[0])
                wav_file = file.replace(".split", ".wav")
                add_whitenoise(wav_file, dest.replace(".split", ".wav"), -22)
                
                # Copy split and text files
                shutil.copy(file, dest)
                
                txt_file = file.replace(".split", ".txt")
                if EXCLUDE_FROM_LM:
                    data = load_text_data(txt_file)
                    with open(dest.replace(".split", ".txt"), 'w') as fout:
                        fout.write("{parser: no-lm}\n\n")
                        for line in data:
                            fout.write(f"{line[0]}\n")
                else:
                    shutil.copy(txt_file, dest.replace(".split", ".txt"))
