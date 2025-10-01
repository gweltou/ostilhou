#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create an aligned file (`srt` or `ali`) from an audio file
and a text file, using a Vosk model (forced alignment).

Usage:
    ./aligner.py audio_file text_file
    
Author:  Gweltaz Duval-Guennoc
"""

SHOW_PROGRESS_BAR = True


import sys
import datetime
import argparse
import srt
import os.path
import json

from ostilhou.asr.aligner import (
    align,
    add_reliability_score,
    resolve_boundaries,
    get_prev_word_idx, get_next_word_idx,
    count_aligned_utterances,
    get_unaligned_ranges,
)
from ostilhou.asr.recognizer import transcribe_file_timecoded
from ostilhou.asr.models import load_model
from ostilhou.asr.dataset import format_timecode, METADATA_PATTERN, extract_metadata
from ostilhou.text import split_sentences, sentence_stats, normalize_sentence
from ostilhou.utils import read_file_drop_comments


autocorrect = False
positional_weight = 0.1



def save(args, hyp, matches):
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
    

    fout = open(args.output, 'w', encoding='utf-8') if args.output else sys.stdout

    if args.type == "srt":
        subs = []
        last = -1
        for match in matches:
            if match["reliability"] == 'X':
                continue
            span = match["span"]
            start = hyp[span[0]]["start"]
            if start <= last: # Avoid timecode overlap
                start += 0.05
            end = hyp[span[1]-1]["end"]
            last = end
            s = srt.Subtitle(index=len(subs),
                    content=match["sentence"],
                    start=datetime.timedelta(seconds=start),
                    end=datetime.timedelta(seconds=end))
            subs.append(s)

        print(srt.compose(subs), file=fout)
    

    elif args.type == "seg":
        # utts = []
        for match in matches:
            if match["reliability"] == 'X':
                continue
            span = match["span"]
            start = int(hyp[span[0]]["start"] * 1000)
            end = int(hyp[span[1]-1]["end"] * 1000)
            print(f"{match["sentence"]} {{start: {start}; end: {end}}}", file=fout)
    

    elif args.type == "ali":
        print(f"{{audio-path: {os.path.basename(args.audio_file)}}}\n\n", file=fout)

        for match in matches:
            if match["reliability"] in ('X', '?'):
                if not args.aligned_only:
                    print(f"{match['sentence'].strip()}", file=fout)
                if not args.force_timecodes:
                    continue

            span = match["span"]
            start = hyp[span[0]]["start"]
            end = hyp[span[1]-1]["end"]
            print(f"{match["sentence"]} {{start: {format_timecode(start)}; end: {format_timecode(end)}}}",
                  file=fout)
    
    if args.output:
        fout.close()


def normalize_lines(lines: list[str]) -> list[str]:
    """Normalize text but keep the metadata untouched"""
    normalized = []
    for line in lines:
        text, metadata = extract_metadata(line)
        if sentence_stats(text)["decimal"] > 0:
            text = normalize_sentence(text, autocorrect=autocorrect)
            prefix = f"{{spk: {metadata['speaker']}}}" if "speaker" in metadata else ''
            normalized.append(f"{prefix} {text}".strip())
        else:
            normalized.append(line)
    return normalized


def get_args():
    parser = argparse.ArgumentParser(
        prog = "Linennan",
        description = "Create a timecoded file (`srt`, `seg` or `ali` file) from an audio file and a text file")
    parser.add_argument("audio_file")
    parser.add_argument("text_file")
    parser.add_argument("-m", "--model", default=None,
        help="Vosk model to use for decoding", metavar='MODEL_PATH')
    parser.add_argument("-t", "--type", choices=["srt", "seg", "ali"],
        help="file output type")
    parser.add_argument("-r", "--reformat", action="store_true",
        help="Reformat text file using punctuation, to put one sentence per line")
    parser.add_argument("-n", "--normalize", action="store_true",
        help="Normalize digits into letter form")
    parser.add_argument("--keep-fillers", action="store_true",
        help="Keep verbal fillers ('euh', 'beñ', 'alors', 'kwa'...)")
    parser.add_argument("-o", "--output", help="write to a file")
    parser.add_argument("-d", "--debug", action="store_true",
        help="Display debug information")
    parser.add_argument("--aligned-only", action="store_true",
        help="Don't output ill-aligned sentences")
    parser.add_argument("--force-timecodes", action="store_true",
        help="Outputs the time segment to ill-aligned utterances")

    return parser.parse_args()



if __name__ == "__main__":
    args = get_args()

    if args.reformat:
        # Use punctuation to reformat text to one sentence per line
        with open(args.text_file, 'r', encoding='utf-8') as fin:
            data = ''.join(fin.readlines())
        parts = data.split('\n\n')
        lines = []
        for part in parts:
            lines.extend(split_sentences(part, end=''))
    else:
        lines = read_file_drop_comments(args.text_file)

    if args.normalize:
        lines = normalize_lines(lines)

    # We should extract any non-utterance text (metadata, comments...) at this point,
    # Keeping track of their positions
    # To reinsert them after the alignment
    # (the aligner cannot match unpronunciable text)

    json_path = os.path.splitext(args.output)[0] + ".json" # caching transcript
    if os.path.exists(json_path):
        print("Reading transcript from cache")
        with open(json_path, 'r') as _f:
            hyp = json.load(_f)
    else:
        load_model(args.model)
        print(f"Transcribing...", file=sys.stderr)
        hyp = transcribe_file_timecoded(args.audio_file)

    with open(json_path, 'w') as _f:
        json.dump(hyp, _f)

    print("First iteration...", file=sys.stderr)
    matches = align(
        lines, hyp,
        0, len(hyp),
        positional_weight,
        progress_bar=SHOW_PROGRESS_BAR)

    # Infer the reliability of each location by checking its adjacent neighbours
    add_reliability_score(matches, hyp, verbose=args.debug)
    n_aligned = count_aligned_utterances(matches)

    save(args, hyp, matches)
    if args.debug:
        print(f"{n_aligned} aligned utterances", file=sys.stderr)

    print("Second iteration...", file=sys.stderr)
    unaligned_ranges = get_unaligned_ranges(matches)
    for start_range, end_range in unaligned_ranges:
        if start_range == 0:
            left_word_idx = 0
        else:
            left_word_idx = matches[start_range-1]["span"][1]
        if end_range == len(matches):
            right_word_idx = len(hyp)
        else:
            right_word_idx = matches[end_range]["span"][0]
        if left_word_idx >= right_word_idx:
            continue
        sentences = [m["sentence"] for m in matches[start_range:end_range]]
        sub_matches = align(
            sentences, hyp,
            left_word_idx, right_word_idx,
            positional_weight,
            progress_bar=False)
        for idx in range(start_range, end_range):
            matches[idx] = sub_matches[idx-start_range]

    add_reliability_score(matches, hyp, verbose=args.debug)
    new_n_aligned = count_aligned_utterances(matches)

    save(args, hyp, matches)
    if args.debug:
        print(f"{new_n_aligned} aligned utterances", file=sys.stderr)


    if new_n_aligned != n_aligned:
        print("Third iteration...")
        unaligned_ranges = get_unaligned_ranges(matches, rel=['O'])
        for start_range, end_range in unaligned_ranges:
            left_word_idx = get_prev_word_idx(matches, start_range)
            
            if end_range == len(matches):
                right_word_idx == len(hyp)
            else:
                right_word_idx = matches[end_range]["span"][0]
            if left_word_idx >= right_word_idx:
                continue
            sentences = [m["sentence"] for m in matches[start_range:end_range]]
            sub_matches = align(
                sentences, hyp,
                left_word_idx, right_word_idx,
                positional_weight,
                progress_bar=SHOW_PROGRESS_BAR)
            for idx in range(start_range, end_range):
                matches[idx] = sub_matches[idx-start_range]
        add_reliability_score(matches, hyp, verbose=args.debug)
        n_aligned = new_n_aligned
        new_n_aligned = count_aligned_utterances(matches)

        save(args, hyp, matches)
        if args.debug:
            print(f"{new_n_aligned} aligned utterances")

    ni = 3
    while new_n_aligned > n_aligned:
        ni += 1
        print("Iteration", ni)

        reliable = ['O', 'o'] if ni%2 == 0 else ['O']
        unaligned_ranges = get_unaligned_ranges(matches, rel=reliable)
        for start_range, end_range in unaligned_ranges:
            if start_range == 0:
                left_word_idx = 0
            else:
                left_word_idx = matches[start_range-1]["span"][1]
            if end_range == len(matches):
                right_word_idx == len(hyp)
            else:
                right_word_idx = matches[end_range]["span"][0]
            if left_word_idx >= right_word_idx:
                continue
            sentences = [m["sentence"] for m in matches[start_range:end_range]]
            sub_matches = align(
                sentences, hyp,
                left_word_idx, right_word_idx,
                positional_weight,
                progress_bar=False)
            for idx in range(start_range, end_range):
                matches[idx] = sub_matches[idx-start_range]
        add_reliability_score(matches, hyp, verbose=args.debug)
        n_aligned = new_n_aligned
        new_n_aligned = count_aligned_utterances(matches)

        save(args, hyp, matches)
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
        assert match["span"][0] < match["span"][1], f"wrong segment: {match}"


    # Resolve overlapping matches
    resolve_boundaries(matches)
    for match in matches:
        assert match["span"][0] < match["span"][1], f"wrong segment: {match}"

    if args.debug:
        for i, match in enumerate(matches):
            print(f"{i} {match["span"]}\t{match["reliability"]}")

    # print(f"Mean CER: {calculate_cer(matches):0.3}", file=sys.stderr)
    n = 0
    for i, match in enumerate(matches):
        if match["reliability"] in ('X', '/', '?'):
            n += 1
    print(f"{n} ill-aligned segment{'s' if n>1 else ''}", file=sys.stderr)

    save(args, hyp, matches)
