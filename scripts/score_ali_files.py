#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Score every utterance of every data item in a given folder
    Creates a TSV file with the following columns :
    filepath, audio ext, seg start, seg end, reference, hypothesis, WER, CER
"""


import sys
import argparse
import os

from colorama import Fore

from ostilhou.utils import list_files_with_extension
from ostilhou.text import pre_process, filter_out_chars, normalize_sentence, PUNCTUATION
from ostilhou.asr import load_ali_file
from ostilhou.asr.recognizer import transcribe_segment
from ostilhou.asr.dataset import format_timecode
from ostilhou.audio import (
    AUDIO_FORMATS,
    find_associated_audiofile,
    load_audiofile, get_audio_segment
)


from jiwer import wer, cer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score every utterance of every data item in a given folder")
    parser.add_argument("data_folder", metavar='FOLDER', help="Folder containing data files")
    parser.add_argument("-o", "--output", type=str, help="Results file")
    args = parser.parse_args()

    # print(args.data_folder)
    if os.path.isdir(args.data_folder):
        ali_files = list_files_with_extension('.ali', args.data_folder)
    elif args.data_folder.lower().endswith('.ali'):
        ali_files = [args.data_folder]
    else:
        print("Wrong argument", file=sys.stderr)
        sys.exit(1)
    
    if args.output and os.path.exists(args.output):
        # Remove already seen files from list
        ali_files = set(ali_files)
        seen_files = set()
        with open(args.output, 'r', encoding='utf-8') as fin:
            for datapoint in fin.readlines():
                path = datapoint.split('\t')[0]
                seen_files.add(path)
        for filepath in seen_files:
            print(f"* Skipping {os.path.split(filepath)[1]}")
        ali_files.difference_update(seen_files)
            

    for filepath in sorted(ali_files):
        _, basename = os.path.split(filepath)
        basename, _ = os.path.splitext(basename)
        print(f"==== {basename} ====", file=sys.stderr)

        ali_data = load_ali_file(filepath)

        audio_file = find_associated_audiofile(filepath, silent=True)
        if not audio_file:
            continue

        segments = ali_data["segments"]
        text = ali_data["sentences"]
        print(len(segments), "utterances", file=sys.stderr)
        if len(segments) == 0:
            print(Fore.RED + f"Error with file {filepath}" + Fore.RESET)
            continue
        audio_ext = os.path.splitext(audio_file)[1][1:]

        audio = load_audiofile(audio_file)

        references = []
        hypothesis = []
        rows = []

        for i in range(len(segments)):
            sentence = filter_out_chars(text[i], PUNCTUATION + '*')
            sentence = normalize_sentence(sentence, autocorrect=True)
            sentence = pre_process(sentence).replace('-', ' ').lower()
            audio_segment = get_audio_segment(i, audio, segments)
            transcription = transcribe_segment(audio_segment)
            transcription = ' '.join(transcription)
            transcription = transcription.replace('-', ' ').lower()
            score_wer = round(wer(sentence, transcription), 2)
            score_cer = round(cer(sentence, transcription), 2)
            if not transcription:
                transcription = '-'
            
            start = format_timecode(segments[i][0])
            end = format_timecode(segments[i][1])
            references.append(sentence)
            hypothesis.append(transcription)
            datapoint = (filepath, audio_ext, start, end, sentence, transcription, str(score_wer), str(score_cer))

            if not args.output:
                print('\t'.join(datapoint))
            else:
                print('.', end='', flush=True)
                rows.append('\t'.join(datapoint))
        
        if args.output:
            print()
            with open(args.output, 'a', encoding='utf-8') as fout:
                for row in rows:
                    fout.write(row + '\n')

        print("  => WER:", wer(references, hypothesis), file=sys.stderr)
        print("  => CER:", cer(references, hypothesis), file=sys.stderr)
