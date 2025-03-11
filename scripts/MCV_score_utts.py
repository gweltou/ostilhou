#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Score every utterance of every data item in a given TSV file

The "all" dataset (for training) is made of "train.tsv", "other.tsv" and "invalidated.tsv"

Usage:
    $ ./score_cv_utterances.py dataset.tsv
"""


import sys
import argparse
import os

from ostilhou.utils import list_files_with_extension
from ostilhou.text import pre_process, filter_out_chars, normalize_sentence, PUNCTUATION
from ostilhou.asr import load_segments_data, load_text_data
from ostilhou.asr.recognizer import transcribe_file, load_model
from ostilhou.audio import load_audiofile, get_audio_segment
from jiwer import wer, cer



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score every utterance of every data item in a given tsv file")
    parser.add_argument("tsv_files", metavar='TSV_FILE', nargs='+', help="A MVC tsv file")
    parser.add_argument("-m", "--model", help="Specify a VOSK model")
    parser.add_argument("-v", "--mcv-version", help="Version of Mozilla Common Voice", type=int)
    # parser.add_argument("-he", "--higher", help="Keeps only over a given CER", default=1.0)
    args = parser.parse_args()

    all_references = []
    all_hypothesis = []
    
    clips_folder = os.path.split(args.tsv_files[0])[0] + "/clips"
    
    already_seen = set()
    
    # Avoid those sentences
    blacklisted_sentences_file = "blacklisted_sentences.txt"
    blacklisted_sentences = []
    if os.path.exists(blacklisted_sentences_file):
        with open(blacklisted_sentences_file, 'r') as f:
            blacklisted_sentences = [l.strip() for l in f.readlines() if not l.startswith('#')]
    else:
        print("Blacklisted sentences file not found")
        
    n_bl = 0
    n_dup = 0
    
    load_model(args.model)

    # print(args.data_folder)
    for tsv_file in args.tsv_files:
        with open(tsv_file, 'r') as tsv:
            tsv.readline() # skip header
            data = tsv.readlines()
        
        data = [ row.strip().split('\t') for row in data ]
        
        for row in data:
            # TSV Fields (< v18) :
            # client_id  path  sentence  up_votes  down_votes  age  gender  accents  variant  locale  segment
            # (>= v18) :
            # client_id  path  sentence_id  sentence  sentence_domain  up_votes  down_votes  age  gender  accents  variant  locale  segment
            
            clip_path = row[1]
            clip_full_path = os.path.join(clips_folder, clip_path)
            
            if args.mcv_version and args.mcv_version < 18:
                text_gt = row[2]
            else:
                text_gt = row[3]
            
            if text_gt in blacklisted_sentences:
                n_bl += 1
                continue
            
            if clip_path in already_seen:
                n_dup += 1
                continue
            
            text_gt = filter_out_chars(text_gt, PUNCTUATION + '*')
            text_gt = normalize_sentence(text_gt, autocorrect=True)
            text_gt = pre_process(text_gt).replace('-', ' ').lower()
            
            text_hyp = ' '.join(transcribe_file(clip_full_path))
            text_hyp = text_hyp.replace('-', ' ').lower()
            
            score_wer = wer(text_gt, text_hyp)
            score_cer = cer(text_gt, text_hyp)
            
            print(f"{clip_path}\t{score_wer:0.3}\t{score_cer:0.3}\t{text_gt}\t{text_hyp}")
            
            already_seen.add(clip_path)
    
    print(f"Number of blacklisted sentences found: {n_bl}", file=sys.stderr)
    print(f"Number of duplicate sentences found: {n_dup}", file=sys.stderr)
