#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Score every utterance in a CSV/TSV file ("path\tsentence\n")
    Creates a TSV file with the following columns :
    filepath, audio ext, seg start, seg end, reference, hypothesis, WER, CER
"""


import sys
import argparse
import os

from colorama import Fore
from ostilhou.text import pre_process, filter_out_chars, normalize_sentence, PUNCTUATION
from ostilhou.asr.recognizer import transcribe_file

from jiwer import wer, cer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score every utterance in a CSV/TSV file")
    parser.add_argument("filename", help="CSV/TSV file")
    parser.add_argument("-o", "--output", type=str, help="Results file")
    args = parser.parse_args()

    root_folder = os.path.split(args.filename)[0]

    audio_files = []
    sentences = []
    hypothesis = []

    with open(args.filename, 'r', encoding='utf-8') as fin:
        for line in fin.readlines():
            path, sentence = line.strip().split('\t')
            audio_files.append(path)
            sentences.append(sentence)

    
    seen_files = set()
    if args.output and os.path.exists(args.output):
        # Remove already seen files from list
        # ali_files = set(ali_files)
        with open(args.output, 'r', encoding='utf-8') as fin:
            for datapoint in fin.readlines():
                path = datapoint.split('\t')[0]
                seen_files.add(path)
            
    audio_files, sentences = zip(*sorted(zip(audio_files, sentences)))

    for filepath, sentence in zip(audio_files, sentences):
        _, basename = os.path.split(filepath)
        basename, _ = os.path.splitext(basename)
        audio_ext = os.path.splitext(filepath)[1][1:]

        path = os.path.join(root_folder, filepath)
        hyp = ' '.join(transcribe_file(path))
        if not hyp: hyp = '-'

        hypothesis.append(hyp)

        sentence = filter_out_chars(sentence, PUNCTUATION + '*')
        sentence = normalize_sentence(sentence, autocorrect=True)
        sentence = pre_process(sentence).replace('-', ' ').lower()

        hyp = hyp.replace('-', ' ').lower()
        score_wer = round(wer(sentence, hyp), 2)
        score_cer = round(cer(sentence, hyp), 2)

        datapoint = (filepath, audio_ext, '', '', sentence, hyp, str(score_wer), str(score_cer))

        if not args.output:
            print('\t'.join(datapoint))
        else:
            print('.', end='', flush=True)
            with open(args.output, 'a', encoding='utf-8') as fout:
                fout.write('\t'.join(datapoint) + '\n')

    print()
    print("  => WER:", wer(list(sentences), hypothesis), file=sys.stderr)
    print("  => CER:", cer(list(sentences), hypothesis), file=sys.stderr)
