#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os.path
from os import makedirs
import shutil

from ostilhou.utils import list_files_with_extension
from ostilhou.audio import add_whitenoise


FOLDER = "#brezhoneg"
DEST = "augmented"


if __name__ == "__main__":

    files = list_files_with_extension('.wav', FOLDER)
    for file in files:
        components = file.split(os.path.sep)
        dest = os.path.join( *([DEST] + components[1:]) )
        makedirs(os.path.split(dest)[0])
        add_whitenoise(file, dest, -20)
        
        # Copy text and split files
        shutil.copy(file.replace(".wav", ".txt"), dest.replace(".wav", ".txt"))
        shutil.copy(file.replace(".wav", ".split"), dest.replace(".wav", ".split"))
