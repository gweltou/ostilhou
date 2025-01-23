#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Score every utterance of every data item in a given folder
    Creates a TSV file with the following columns :
    filepath, audio ext, seg start, seg end, reference, hypothesis, WER, CER
    
    usage:
        python3 score_ali_files.py data_folder/
        python3 score_ali_files.py data.ali
        python3 score_ali_files.py list_of_files.txt
"""


import sys
import argparse
import os
from jiwer import wer, cer
from tempfile import mkstemp

from ostilhou.utils import (
    list_files_with_extension,
    red,
    yellow,
)
from ostilhou.text import (
    pre_process, filter_out_chars, normalize_sentence,
    sentence_stats,
    PUNCTUATION,
)
from ostilhou.asr import load_ali_file
from ostilhou.asr.models import load_model
from ostilhou.asr.recognizer import transcribe_segment
from ostilhou.asr.dataset import format_timecode
from ostilhou.audio import load_audiofile, get_audio_segment, add_whitenoise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score every utterance of every ALI file in a given folder"
    )
    parser.add_argument("data_folder", metavar='FOLDER',
        help="Folder containing ALI files or a single ALI file or a text file with a list of paths in it")
    parser.add_argument("-m", "--model", default=None,
        help="Vosk model to use for decoding", metavar='MODEL_PATH')
    parser.add_argument("-o", "--output", type=str, help="Results file")
    parser.add_argument("--noise", type=float, help="Add white noise to audio (dB)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    
    load_model(args.model)

    if os.path.isdir(args.data_folder):
        ali_files = list_files_with_extension('.ali', args.data_folder)
    elif args.data_folder.lower().endswith('.ali'):
        ali_files = [args.data_folder]
    elif os.path.isfile(args.data_folder):
        # A text file with a path to an ALI file on every line
        with open(args.data_folder, 'r') as _f:
            ali_files = [ l.strip() for l in _f.readlines() ]
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
            print(f"* Skipping {os.path.split(filepath)[1]}", file=sys.stderr)
        ali_files.difference_update(seen_files)
            
    wer_sum = 0.0
    cer_sum = 0.0
    words_sum = 0
    letters_sum = 0
    for filepath in sorted(ali_files):
        _, basename = os.path.split(filepath)
        basename, _ = os.path.splitext(basename)
        print(f"==== {basename} ====", file=sys.stderr)

        ali_data = load_ali_file(filepath)
        audio_path = ali_data["audio_path"]
        if not audio_path:
            print(red("Couldn't fine associated audiofile"), file=sys.stderr)
            continue

        if args.noise:
            print(yellow(f"Adding white noise to audio ({args.noise} dB)"))
            _, noisy_audio_path = mkstemp()
            add_whitenoise(audio_path, noisy_audio_path, min(args.noise, 0))
            audio_path = noisy_audio_path

        segments = ali_data["segments"]
        text = ali_data["sentences"]
        if args.verbose:
            print(f"  {len(segments)} utterances", file=sys.stderr)
        if len(segments) == 0:
            print(red(f"Error with file {filepath}"))
            continue
        audio_ext = os.path.splitext(audio_path)[1][1:]

        audio = load_audiofile(audio_path)

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
            stats = sentence_stats(sentence)
            wer_sum += score_wer * stats["words"]
            cer_sum += score_cer * stats["letter"]
            words_sum += stats["words"]
            letters_sum += stats["letter"]
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
        
        if args.noise:
            # Remove temporary noisy audio
            os.remove(noisy_audio_path)

        print("  => WER:", round(wer(references, hypothesis), 3), file=sys.stderr)
        print("  => CER:", round(cer(references, hypothesis), 3), file=sys.stderr)

    print(f"\n======== TOTAL ({os.path.split(args.model)[1]}) ========", file=sys.stderr)
    print(f"WER: {round(wer_sum / words_sum, 3)}", file=sys.stderr)
    print(f"CER: {round(cer_sum / letters_sum, 3)}", file=sys.stderr)
    print("\n", file=sys.stderr)