#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create subtitles (a `srt` file) from an audio file
and a text file, using a vosk model

Author:  Gweltaz Duval-Guennoc

Usage: ./linennan.py audio_file text_file

"""


import sys
import datetime
import argparse
import srt
import os.path

from ostilhou.asr.aligner import align, add_reliability_score, resolve_boundaries
from ostilhou.asr.recognizer import transcribe_file_timecoded
from ostilhou.asr.models import load_model, DEFAULT_MODEL
from ostilhou.asr.dataset import format_timecode
from ostilhou.text import split_sentences
from ostilhou.utils import read_file_drop_comments


autocorrect = False
positional_weight = 0.1



def count_aligned_utterances(matches):
    n = 0
    for match in matches:
        if match["reliability"] in ('O',):
            n += 1
    return n


def get_unaligned_ranges(sentences, matches, rel=['O']):
    # Find ill-aligned sentence ranges
    wrong_ranges = []
    start = 0
    end = 0
    while True:
        while start < len(sentences) and matches[start]["reliability"] in rel:
            start += 1
        end = start
        while end < len(sentences) and matches[end]["reliability"] not in rel:
            end += 1
        if start >= len(sentences):
            break
        wrong_ranges.append((start, end))
        start = end
    return wrong_ranges



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "Linennan",
        description = "Create a timecoded file (`srt`, `seg` or `ali` file) from an audio file and a text file")
    parser.add_argument("audio_file")
    parser.add_argument("text_file")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL,
        help="Vosk model to use for decoding", metavar='MODEL_PATH')
    parser.add_argument("-t", "--type", choices=["srt", "seg", "ali"],
        help="file output type")
    parser.add_argument("-r", "--reformat", action="store_true",
        help="reformat text file using punctuation, to put one sentence per line")
    parser.add_argument("--keep-fillers", action="store_true",
        help="Keep verbal fillers ('euh', 'beñ', 'alors', 'kwa'...)")
    parser.add_argument("-o", "--output", help="write to a file")
    parser.add_argument("-d", "--debug", action="store_true",
        help="display debug information")
    parser.add_argument("-f", "--force-output", action="store_true",
        help="Output ill-aligned sentences as well")
    args = parser.parse_args()


    load_model(args.model)

    lines = read_file_drop_comments(args.text_file)

    if args.reformat:
        # Use punctuation to reformat text to one sentence per line
        with open(args.text_file, 'r') as fin:
            data = ''.join(fin.readlines())
        parts = data.split('\n\n')
        lines = []
        for part in parts:
            lines.extend(split_sentences(part, end=''))
    else:
        lines = read_file_drop_comments(args.text_file)


    hyp = transcribe_file_timecoded(args.audio_file)

    matches = align(lines, hyp, 0, len(hyp), positional_weight)

    # Infer the reliability of each location by checking its adjacent neighbours
    add_reliability_score(matches, hyp, verbose=args.debug)
    n_aligned = count_aligned_utterances(matches)
    if args.debug:
        print(f"{n_aligned} aligned utterances", file=sys.stderr)

    print("Second iteration", file=sys.stderr)
    unaligned_ranges = get_unaligned_ranges(lines, matches)
    for start_range, end_range in unaligned_ranges:
        if start_range == 0:
            left_word_idx = 0
        else:
            left_word_idx = matches[start_range-1]["span"][1]
        if end_range == len(lines):
            right_word_idx = len(hyp)
        else:
            right_word_idx = matches[end_range]["span"][0]
        if left_word_idx >= right_word_idx:
            continue
        sub_matches = align(
            lines[start_range: end_range], hyp,
            left_word_idx, right_word_idx, positional_weight)
        for idx in range(start_range, end_range):
            matches[idx] = sub_matches[idx-start_range]

    add_reliability_score(matches, hyp, verbose=args.debug)
    new_n_aligned = count_aligned_utterances(matches)
    if args.debug:
        print(f"{new_n_aligned} aligned utterances", file=sys.stderr)

    if new_n_aligned != n_aligned:
        print("Third iteration")
        unaligned_ranges = get_unaligned_ranges(lines, matches, rel=['O'])
        for start_range, end_range in unaligned_ranges:
            if start_range == 0:
                left_word_idx = 0
            else:
                left_word_idx = matches[start_range-1]["span"][1]
            if end_range == len(lines):
                right_word_idx == len(hyp)
            else:
                right_word_idx = matches[end_range]["span"][0]
            if left_word_idx >= right_word_idx:
                continue
            sub_matches = align(
                lines[start_range: end_range], hyp,
                left_word_idx, right_word_idx, positional_weight)
            for idx in range(start_range, end_range):
                matches[idx] = sub_matches[idx-start_range]
        add_reliability_score(matches, hyp, verbose=args.debug)
        n_aligned = new_n_aligned
        new_n_aligned = count_aligned_utterances(matches)

        if args.debug:
            print(f"{new_n_aligned} aligned utterances")

    ni = 3
    while new_n_aligned > n_aligned:
        ni += 1
        print("Iteration", ni)

        reliable = ['O', 'o'] if ni%2 == 0 else ['O']
        unaligned_ranges = get_unaligned_ranges(lines, matches, rel=reliable)
        for start_range, end_range in unaligned_ranges:
            if start_range == 0:
                left_word_idx = 0
            else:
                left_word_idx = matches[start_range-1]["span"][1]
            if end_range == len(lines):
                right_word_idx == len(hyp)
            else:
                right_word_idx = matches[end_range]["span"][0]
            if left_word_idx >= right_word_idx:
                continue
            sub_matches = align(
                lines[start_range: end_range], hyp,
                left_word_idx, right_word_idx, positional_weight)
            for idx in range(start_range, end_range):
                matches[idx] = sub_matches[idx-start_range]
        add_reliability_score(matches, hyp, verbose=args.debug)
        n_aligned = new_n_aligned
        new_n_aligned = count_aligned_utterances(matches)

        if args.debug:
            print(f"{new_n_aligned} aligned utterances", file=sys.stderr)


    # Invalidate semi-reliable segments that doesn't fit
    # with previously accespted semi-reliable segments
    last_reliable_idx = 0
    for match in matches:
        if match["reliability"] in ('o', 'O'):
            if match["span"][0] >= last_reliable_idx:
                last_reliable_idx = match["span"][1]
            else:
                match["reliability"] = '?'


    # Resolve overlapping matches
    resolve_boundaries(matches)

    if args.debug:
        for i, match in enumerate(matches):
            print(f"{i} {match["span"]}\t{match["reliability"]}")

    # print(f"Mean CER: {calculate_cer(matches):0.3}", file=sys.stderr)
    n = 0
    for i, l in enumerate(lines):
        if matches[i]["reliability"] in ('X', '/', '?'):
            n += 1
    print(f"{n} ill-aligned segment{'s' if n>1 else ''}", file=sys.stderr)


    # Resolve file output type
    if args.output and not args.type:
        # No type explicitely defined, use output file extension
        split_ext = args.output.rsplit('.', maxsplit=1)
        if len(split_ext) == 2:
            ext = split_ext[1].lower()
            if ext in ("srt", "seg", "ali"):
                args.type = ext
            else:
                print("Unrecognized extension, using default type (`srt`)", file=sys.stderr)
                args.type = "srt"
        else:
            # No file extension found, use default type
            args.type = "srt"

    if not args.type:
        args.type = "srt"
    

    fout = open(args.output, 'w') if args.output else sys.stdout

    if args.type == "srt":
        subs = []
        last = -1
        for i, line in enumerate(lines):
            if matches[i]["reliability"] == 'X':
                continue

            span = matches[i]["span"]
            start = hyp[span[0]]["start"]
            if start <= last: # Avoid timecode overlap
                start += 0.05
            end = hyp[span[1]-1]["end"]
            last = end
            s = srt.Subtitle(index=len(subs),
                    content=line,
                    start=datetime.timedelta(seconds=start),
                    end=datetime.timedelta(seconds=end))
            subs.append(s)

        print(srt.compose(subs), file=fout)
    

    elif args.type == "seg":
        # utts = []
        for i, line in enumerate(lines):
            if matches[i]["reliability"] == 'X':
                continue

            span = matches[i]["span"]
            start = int(hyp[span[0]]["start"] * 1000)
            end = int(hyp[span[1]-1]["end"] * 1000)
            print(f"{line} {{start: {start}; end: {end}}}", file=fout)
    

    elif args.type == "ali":
        print(f"{{audio-path: {os.path.basename(args.audio_file)}}}\n\n", file=fout)

        for i, line in enumerate(lines):
            if matches[i]["reliability"] in ('X', '?'):
                if args.force_output:
                    print(f"{line.strip()}", file=fout)
                continue

            span = matches[i]["span"]
            start = hyp[span[0]]["start"]
            end = hyp[span[1]-1]["end"]
            print(f"{line.strip()} {{start: {format_timecode(start)}; end: {format_timecode(end)}}}",
                  file=fout)
    

    if args.output:
        fout.close()