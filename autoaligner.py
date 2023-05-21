#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Autoaligner using vosk model

Author:  Gweltaz Duval-Guennoc

Usage: ./autoaligner split_file

TODO :
    * tretañ ar c'hemadurioù : vMickaël, dTouène
    * Niverennoù -> stumm skrid
"""


import os
import sys
import re
sys.path.append("../..")
from libMySTT import load_segments, transcribe_segment, get_cleaned_sentence
from pydub import AudioSegment
import jiwer


# KEMMADUR_PATTERN = re.compile(r" (g|b|d|w|v|c'h){1}/[a-zñ']{3,}", re.IGNORECASE)
KEMMADUR_PATTERN = re.compile(r"(vM|dT)")
"""
M -> V
T -> D
"""


if __name__ == "__main__":
    split_filename = os.path.abspath(sys.argv[1])
    rep, filename = os.path.split(split_filename)
    recording_id = filename.split(os.path.extsep)[0]
    wav_filename = os.path.join(rep, os.path.extsep.join((recording_id, 'wav')))
    text_filename = os.path.join(rep, os.path.extsep.join((recording_id, 'txt')))
    gt_filename = os.path.join(rep, os.path.extsep.join((recording_id + "_raw", 'txt')))
    # transcript_filename = os.path.join(rep, os.path.extsep.join((recording_id + "_transcript", 'txt')))

    segments, _ = load_segments(split_filename)
    song = AudioSegment.from_wav(wav_filename)

    # Read ground-truth file and concatenate all lines as a single line.
    # header = []
    with open(gt_filename, 'r') as f:
        lines = f.readlines()
    ground_truth = " ".join([line.strip() for line in lines])
    ground_truth = ground_truth.replace('- ', '-')
    ground_truth = ground_truth.replace('/ ', '/')

    # for match in KEMMADUR_PATTERN.finditer(ground_truth):
    #     print(match)

    # Automatic alignment
    aligned = []
    token_i = 0
    ground_truth_tokens = ground_truth.split()
    # for hyp_sentence in transcription:
    for i, (s, e) in enumerate(segments):
        # Transcription with Vosk model
        hyp_sentence = transcribe_segment(song[s:e])
        # Compare hyp sentence (fixed size) with tokens from ground-truth
        # by appending a single token from ground-truth until CER score is
        # at a local minima
        # for i in range( int( len(hyp_sentence.split()) + 5 ) ):
        gt_lookup_tokens = []
        best_cer_score = 999
        best_match = []
        while True and token_i < len(ground_truth_tokens):
            gt_lookup_tokens.append(ground_truth_tokens[token_i])
            gt_cleaned = get_cleaned_sentence( ' '.join(gt_lookup_tokens) )[0]
            cer_score = jiwer.cer(gt_cleaned, hyp_sentence)
            if cer_score > best_cer_score:
                # CER starts to increase, keep last proposition
                # and stop looking further
                gt_lookup_tokens.pop()
                best_match = gt_lookup_tokens
                break
            best_cer_score = cer_score
            best_match = gt_lookup_tokens
            token_i += 1
        
        # Check if CER score can still be lowered by truncating the beggining
        # of the matched ground-truth
        while True and len(gt_lookup_tokens) > 1:
            gt_lookup_tokens = gt_lookup_tokens[1:]
            gt_cleaned = get_cleaned_sentence(' '.join(gt_lookup_tokens))[0]
            cer_score = jiwer.cer(gt_cleaned, hyp_sentence)
            if cer_score >= best_cer_score:
                break
            best_cer_score = cer_score
            best_match = gt_lookup_tokens

        aligned.append(' '.join(best_match) + '\n')
        if best_cer_score > 0.0:
            print(f"{i+1}> Score: {best_cer_score:.3f}")
            print("G-T:", ' '.join(best_match))
            print("HYP:", hyp_sentence)
            print()

    with open(text_filename, 'w') as f:
        f.writelines(aligned)