#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Score every utterance of every data item in a given folder

DEPRECATED
"""


import sys
import argparse
import os

from ostilhou.utils import list_files_with_extension
from ostilhou.text import pre_process, filter_out_chars, normalize_sentence, PUNCTUATION
from ostilhou.asr import load_segments_data, load_text_data
from ostilhou.asr.recognizer import transcribe_segment
from ostilhou.audio import load_audiofile, get_audio_segment
from jiwer import wer, cer



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score every utterance of every data item in a given folder")
    parser.add_argument("data_folder", metavar='FOLDER', help="Folder containing data files")
    parser.add_argument("-u", "--per-utterance", help="Calculate WER and CER score per utterance", action="store_true")
    # parser.add_argument("-he", "--higher", help="Keeps only over a given CER", default=1.0)
    args = parser.parse_args()

    all_references = []
    all_hypothesis = []

    # print(args.data_folder)
    split_files = list_files_with_extension('split', args.data_folder)
    for split_file in sorted(split_files):
        basename, _ = os.path.splitext(split_file)
        wav_file = basename + os.path.extsep + "wav"
        text_file = basename + os.path.extsep + "txt"
        segments = load_segments_data(split_file)
        utterances = load_text_data(text_file)
        song = load_audiofile(wav_file)
        _, basename = os.path.split(basename)
        references = []
        hypothesis = []
        # print("# ==== " + basename + " ====")
        for i in range(len(segments)):
            # sentence, _ = get_cleaned_sentence(utterances[i][0])
            sentence = filter_out_chars(utterances[i][0], PUNCTUATION + '*')
            sentence = normalize_sentence(sentence, autocorrect=True)
            sentence = pre_process(sentence).replace('-', ' ').lower()
            transcription = transcribe_segment(get_audio_segment(i, song, segments))
            transcription = transcription.replace('-', ' ').lower()
            references.append(sentence)
            hypothesis.append(transcription)
            if not args.per_utterance:
                continue
            score_wer = wer(sentence, transcription)
            score_cer = cer(sentence, transcription)
            if not transcription:
                transcription = '-'
            #if score_cer >= 0.2 or score_wer > 0.4:
            # if score_cer >= 1.0:
            print(f"{basename}.{i:03}\t{round(score_wer, 2)}\t{round(score_cer, 2)}\t{sentence}\t{transcription}")
        all_references.extend(references)
        all_hypothesis.extend(hypothesis)

    print("====== OVERALL ======", file=sys.stderr)
    print(len(all_references), "utterances", file=sys.stderr)
    print("WER:", wer(all_references, all_hypothesis), file=sys.stderr)
    print("CER:", cer(all_references, all_hypothesis), file=sys.stderr)
