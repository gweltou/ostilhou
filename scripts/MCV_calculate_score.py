#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from ostilhou.text import sentence_stats



def calculate_score(lines):
    total_words = 0
    total_chars = 0
    total_wer = 0
    total_cer = 0
    
    gt = []
    hyp = []
    
    for line in lines:
        _, wer, cer, gt_sent, hyp_sent = line.split('\t')
        stats = sentence_stats(gt_sent)
        total_words += stats["words"]
        total_chars += stats["letter"]
        total_wer += float(wer) * stats["words"]
        total_cer += float(cer) * stats["letter"]
        gt.append(gt_sent)
        hyp.append(hyp_sent)
        
    print(f"Mean wer: {total_wer/total_words:.2%}")
    print(f"Mean cer: {total_cer/total_chars:.2%}")



if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        lines = f.readlines()
    
    calculate_score(lines)
