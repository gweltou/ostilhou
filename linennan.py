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
from ostilhou.asr.recognizer import transcribe_file_timecode
from ostilhou.text import (
    pre_process, filter_out,
    sentence_stats,
    tokenize, detokenize, normalize_sentence, split_sentences,
    PUNCTUATION
)
from ostilhou.utils import read_file_drop_comments
import jiwer



autocorrect = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "Linennan",
        description = "Create a timecoded file (`srt` or `split` file) from a text and an audio file")
    parser.add_argument("audio_file")
    parser.add_argument("text_file")
    parser.add_argument("-t", "--type", choices=["srt", "split"], help="file output type")
    parser.add_argument("-r", "--reformat", action="store_true", help="reformat text file using punctuation, to put one sentence per line")
    parser.add_argument("-o", "--output", help="write to a file")
    parser.add_argument("-d", "--debug", action="store_true", help="display debug information")
    args = parser.parse_args()


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

    cleaned_lines = [ filter_out(pre_process(line), PUNCTUATION + "><*").strip() for line in lines ]
    
    # Look for numbers in text file, normalize in that case
    normalize = False
    for line in cleaned_lines:
        if sentence_stats(line)["decimal"] > 0:
            normalize = True
            break
    if normalize:
        cleaned_lines = [ normalize_sentence(line, autocorrect=autocorrect) for line in cleaned_lines ]
    
    cleaned_lines = [ " ".join(line.lower().replace('-', ' ').split()) for line in cleaned_lines ]
    # print(cleaned_lines, file=sys.stderr)

    hyp = transcribe_file_timecode(args.audio_file)


    # Try to locate the best match for each sentence in transcription

    sentence_matches = []
    for sentence in cleaned_lines:
        match = []
        for i in range(len(hyp)):
            # Try to find a local minima for the CER by adding one word at a time
            best_score = 999
            offset = 1
            while i+offset <= len(hyp):
                hyp_window = hyp[i: i+offset]
                hyp_sentence = ' '.join( [t["word"].lower().replace('-', ' ') for t in hyp_window] )
                score = jiwer.cer(
                    filter_out(sentence, ' '),
                    filter_out(hyp_sentence, ' ')
                    )
                if score <= best_score:
                    best_score = score
                    best_span = (i, i+offset)
                    best_hyp = hyp_sentence
                else:
                    break
                offset += 1
            
            match.append( {"hyp": best_hyp, "score": best_score, "span": best_span} )
        
        match.sort(key=lambda x: x["score"])
        sentence_matches.append(match[0])


    # Infer the reliability of each location by checking its adjacent neighbours

    def get_prev_wi(idx):
        if idx <= 0:
            return 0
        return sentence_matches[idx-1]["span"][1]
    
    def get_next_wi(idx):
        if idx >= len(sentence_matches) - 1:
            return len(hyp)
        return sentence_matches[idx+1]["span"][0]
    
    reliability = []
    last_reliable_wi = 0
    for i, match in enumerate(sentence_matches):
        span = match["span"]
        is_pdn = get_prev_wi(i) == span[0] # is prev a direct neighbour ?
        is_ndn = get_next_wi(i) == span[1] # is next a direct neighbour ?
        if is_pdn or is_ndn:
            last_reliable_wi = span[1]
            r = 'o' # Semi-reliable
            if is_pdn and is_ndn:
                r = 'O' # Reliable
        elif span[0] > last_reliable_wi:
            r = '?' # Not sure...
        else:
            r = 'X' # Obviously wrong
        reliability.append(r)
        # print(f"{i} {span}\t{r}")
    

    # Now that we have a reliability vector, we can try to deduce
    # the state (right or wrong) of the locations with "unknown" reliability

    def get_prev_reliable_wi(idx):
        if idx <= 0:
            return 0
        for i in range(idx, 0, -1):
            if reliability[i-1] in ('O', 'o'):
                return sentence_matches[i-1]["span"][1]
        return 0

    def get_next_reliable_wi(idx):
        if idx >= len(sentence_matches) - 1:
            return len(hyp)
        for i in range(idx+1, len(reliability)):
            if reliability[i] in ('O', 'o'):
                return sentence_matches[i]["span"][0]
        return len(hyp)

    for i in range(len(sentence_matches)):
        # An "unknown" is validated if it's location is between the
        # previous reliable location and the next reliable location
        # It is deemed as "wrong" otherwise
        if reliability[i] == '?':
            span = sentence_matches[i]["span"]
            p_rel_wi = get_prev_reliable_wi(i)
            n_rel_wi = get_next_reliable_wi(i)
            if p_rel_wi < span[0] and span[1] < n_rel_wi:
                reliability[i] = 'o'
            else:
                reliability[i] = 'X'


    # Try to repair remaining wrong locations
    for i in range(1, len(sentence_matches)-1):
        if reliability[i] == 'X':
            if reliability[i-1] in ('O', 'o') and reliability[i+1] in ('O', 'o'):
                span = (get_prev_wi(i), get_next_wi(i))
                hyp_window = hyp[span[0]: span[1]]
                hyp_sentence = ' '.join( [t["word"].lower().replace('-', ' ') for t in hyp_window] )
                score = jiwer.cer(
                    filter_out(sentence, ' '),
                    filter_out(hyp_sentence, ' ')
                    )
                sentence_matches[i] = {"hyp": hyp_sentence, "score": score, "span": span}
                reliability[i] = '.'


    total_cer = 0
    for i, match in enumerate(sentence_matches):
        total_cer += match["score"]
        if args.debug:
            span = match["span"]
            r = reliability[i]
            print(f"{i} {span}\t{r}", file=sys.stderr)
    print(f"Mean CER: {total_cer / len(sentence_matches):0.3}", file=sys.stderr)

    n = 0
    for i, l in enumerate(cleaned_lines):
        if reliability[i] == 'X':
            hyp_sentence = sentence_matches[i]["hyp"]
            print(f"{i}\t{sentence_matches[i]['span']}\t{l}\t{hyp_sentence}\t", file=sys.stderr)
            n += 1
    print(f"{n} unaligned segment{'s' if n>1 else ''}", file=sys.stderr)



    # Resolve file output type

    if args.output and not args.type:
        # No type explicitely defined, use output file extension
        split_ext = args.output.rsplit('.', maxsplit=1)
        if len(split_ext) == 2:
            ext = split_ext[1].lower()
            if ext in ("srt", "split"):
                args.type = ext
            else:
                print("Unrecognized extension, using default type (`srt`)", file=sys.stderr)
                args.type = 'srt'
        else:
            # No file extension found, use default type
            args.type = 'srt'

    if not args.type:
        args.type = "srt"
    

    fout = open(args.output, 'w') if args.output else sys.stdout

    if args.type == "srt":
        subs = []
        last = -1
        for i, line in enumerate(lines):
            if reliability[i] == 'X':
                continue

            span = sentence_matches[i]["span"]
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
    

    if args.type == "split":
        utts = []
        for i, line in enumerate(lines):
            span = sentence_matches[i]["span"]
            start = int(hyp[span[0]]["start"] * 1000)
            end = int(hyp[span[1]-1]["end"] * 1000)
            print(f"{start} {end}", file=fout)