#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
from jiwer import wer, cer


if __name__ == "__main__":
    
    with open(sys.argv[1], 'r') as fin:
        rows = fin.readlines()
    
    references = []
    hypothesis = []
    last_path = ""
    scores = []

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