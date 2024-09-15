#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
import argparse

from jiwer import wer, cer


"""
    Summerize and sort by WER score a list of utterances from a score file
    created by `score_ali_files.py`
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sort utterances by score from a score file")
    parser.add_argument("filename", help="Score file")
    parser.add_argument("-u", "--per-utterance", help="Calculate WER and CER score per utterance", action="store_true")
    args = parser.parse_args()

    with open(args.filename, 'r') as fin:
        rows = fin.readlines()
    
    references = []
    hypothesis = []
    last_path = ""
    scores = []

    if args.per_utterance:
        data = []
        for row in rows:
            path, audio_ext, _, _, ref, hyp, wer_score, cer_score = row.strip().split('\t')
            data.append( (path, ref, hyp, wer_score, cer_score) )
        data.sort(key=lambda k: k[3])

        for path, ref, hyp, wer_score, cer_score in data:
            print(f"{os.path.split(path)[1]} {wer_score} {cer_score}")
            print(f"{ref} | {hyp}")

    else:
        for row in rows:
            path, audio_ext, _, _, ref, hyp, _, _ = row.split('\t')
            if path != last_path and len(references) > 0:
                document_wer = wer(references, hypothesis)
                document_cer = cer(references, hypothesis)
                scores.append([last_path, document_wer, document_cer])
                references = []
                hypothesis = []
            references.append(ref)
            hypothesis.append(hyp)
            last_path = path
        document_wer = wer(references, hypothesis)
        document_cer = cer(references, hypothesis)
        scores.append([last_path, document_wer, document_cer])
        
        for path, document_wer, document_cer in sorted(scores, key=lambda k: k[1]):
            print(os.path.split(path)[1])
            print(f"    WER {document_wer}, CER {document_cer}")
            print()