#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Converts Mozilla's Spontanous Speech dataset to an ALI file

usage:
    $ python3 unpack.py train.tsv train
    $ python3 unpack.py test.tsv test
    
Author: Gweltaz Duval-Guennoc
"""


import sys
import os
from pathlib import Path

from ostilhou.asr.dataset import create_ali_file, load_ali_file
from ostilhou.audio import convert_to_wav, get_audiofile_length, concatenate_audiofiles



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} data_file.tsv [data_file2.tsv...] SAVE_FOLDER")
        sys.exit(1)
    
    data_folder = os.path.split(sys.argv[1])[0]
    
    dest_folder = sys.argv[-1]
    data_files = sys.argv[1:-1]
    
    clips_folder = Path(data_folder) / "audios"
        
    if not os.path.exists(dest_folder):
        os.mkdir(dest_folder)
    
    for data_file in data_files:
        data = []
        
        data_file = os.path.join(data_folder, data_file)
        print(data_file)
        if os.path.exists(data_file):
            # client_id
            # audio_id
            # audio_file
            # duration_ms
            # prompt_id
            # prompt
            # transcription
            # votes
            # age
            # gender
            # accents
            # variant
            # language
            # prompt_upvotes
            # prompt_reports
            # is_edited	split
            # char_per_sec
            # quality_tags
            with open(data_file, 'r') as f:
                f.readline() # skip header

                l = f.readline().strip()
                while l:
                    l = l.split('\t')
                    data.append(l[:9])  # Keep first 8 fields only
                    l = f.readline().strip()
        else:
            print("File not found:", data_file)
            continue
        
        speakers = set([l[0] for l in data])
        print(f"{len(speakers)} speakers found...")
        
        text = []
        segments = []
        audiofiles = []
        t = 0.0
        for row in data:
            audio_file = clips_folder / row[2]
            audiofiles.append(audio_file)
            
            text.append(row[6])

            nt = t + get_audiofile_length(audio_file)
            segments.append( [t, nt] ) # Offset end of segment by a 0.2 second
            t = nt
                        
        # Concatenate all audio clips
        dest_folder = Path(dest_folder)
        wav_concat_path = dest_folder / "ss_corpus_br.mp3"
        concatenate_audiofiles(audiofiles, str(wav_concat_path))

        # Create the ALI file
        metadata = {
            "media-path": wav_concat_path,
            "licence": "CC0",
            "tags": ["Mozilla Spontaneous Speech"],
        }

        ali_path = dest_folder / "ss_corpus_br.ali"
        ali_data = create_ali_file(text, segments, **metadata)
        with open(ali_path, 'w', encoding='utf-8') as _fout:
            _fout.write(ali_data)
            
        minutes, seconds = divmod(round(t), 60)
        hours, minutes = divmod(minutes, 60)
        print(f"Total clip time kept: {hours}h {minutes}' {seconds}''")