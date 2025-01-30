#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
from random import randint
from os import makedirs
import shutil
import argparse

from ostilhou.audio import add_whitenoise, add_random_amb_noise
from ostilhou.asr import load_text_data, load_ali_file, create_ali_file


"""
Data Augmentation by adding noise to audiofiles

Usage:
    python3 noise_augment.py file_list.txt [-o output_dir]

"""


EXCLUDE_FROM_LM = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filelist", help="List of files to be augmented, in text format")
    parser.add_argument("--amb-noise", action="store_true", help="Augment by adding ambiance noise")
    parser.add_argument("-o", "--output", help="Path where to write the augmented files",
                        default=os.path.join(os.getcwd(), "augmented_noise"))
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
            # Old formats
            soundfile = filepath.replace(file_ext, ".wav")
        
        utterance_file_dest = os.path.join(args.output, filename)
        soundfile_dest = os.path.join(args.output, os.path.split(soundfile)[1])
        if not soundfile_dest.lower().endswith(".wav"):
            basename, _ = os.path.splitext(soundfile_dest)
            soundfile_dest = basename + ".wav"

        if not os.path.exists(utterance_file_dest):
            makedirs(args.output, exist_ok=True)
            print(filepath)

            if args.amb_noise:
                add_random_amb_noise(soundfile, soundfile_dest, randint(-10, -4))
                soundfile = soundfile_dest
            
            add_whitenoise(soundfile, soundfile_dest, randint(-28, -20))
            

            if file_ext.lower() == ".ali":
                with open(utterance_file_dest, 'w', encoding="utf-8") as _f:
                    _f.write(
                        create_ali_file(
                            ali_data["sentences"],
                            ali_data["segments"],
                            audio_path=os.path.split(soundfile_dest)[1],
                            parser="no-lm"))
            else:
                # Old format
                # Copy split and text files
                shutil.copy(filepath, utterance_file_dest)
                txt_file = filepath.replace(file_ext, ".txt")
                if EXCLUDE_FROM_LM:
                    data = load_text_data(txt_file)
                    with open(utterance_file_dest.replace(file_ext, ".txt"), 'w', encoding='utf-8') as fout:
                        fout.write("{parser: no-lm}\n\n")
                        for line in data:
                            fout.write(f"{line[0]}\n")
                else:
                    shutil.copy(txt_file, utterance_file_dest.replace(file_ext, ".txt"))
