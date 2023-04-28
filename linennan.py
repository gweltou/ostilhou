#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create subtitles (a `srt` file) from an audio file
and a text file, using a vosk model

Author:  Gweltaz Duval-Guennoc

Usage: ./linennan_txt2srt.py audio_file text_file

TODO :
    * tretañ ar c'hemadurioù : vMickaël, dTouène
    * Niverennoù -> stumm skrid
"""


import os
import sys
import re
import datetime
import argparse
import srt
sys.path.append("../..")
from libMySTT import get_cleaned_sentence
from pydub import AudioSegment
from ostilhou.asr import load_segments_data
from ostilhou.asr.recognizer import transcribe_file_timecode
from ostilhou.text import pre_process, filter_out, sentence_stats, PUNCTUATION
import jiwer


# KEMMADUR_PATTERN = re.compile(r" (g|b|d|w|v|c'h){1}/[a-zñ']{3,}", re.IGNORECASE)
KEMMADUR_PATTERN = re.compile(r"(vM|dT)")
"""
M -> V
T -> D
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "Linennan",
        description = "Create a timecoded file (`srt` or `split` file) from a properly segmented text file and an audio file")
    parser.add_argument("audio_file")
    parser.add_argument("text_file")
    parser.add_argument("-t", "--type", choices=["srt", "split"], default="srt")
    parser.add_argument("-o", "--output", help="output file")
    args = parser.parse_args()
    print(args)

    # if len(sys.argv) < 3:
    #     print("Usage: ./linennan_txt2srt.py audio_file text_file")
    # audio_filename = os.path.abspath(sys.argv[1])
    # text_filename = os.path.abspath(sys.argv[2])
    
    with open(args.text_file, 'r') as f:
        lines = f.readlines()
    cleaned_lines = [ filter_out(pre_process(line), PUNCTUATION + "><").strip() for line in lines ]
    cleaned_lines = [ " ".join(line.lower().replace('-', ' ').split()) for line in cleaned_lines ]

    # Look for numbers in text file
    normalize = False
    for line in cleaned_lines:
        if sentence_stats(line)["decimal"] > 0:
            normalize = True
            break

    hyp = transcribe_file_timecode(args.audio_file, normalize=normalize)

    line_matches = []

    for sentence in cleaned_lines:
        l = len(sentence.split())
        matches = []    # {"score": , "span":(s,e),}
        for i in range(len(hyp) - l):
            span = (i, i+l) # Span is in word indices
            hyp_window = hyp[i: i+l]
            # Character compare score without spaces
            hyp_sentence = ' '.join( [t["word"].lower().replace('-', ' ') for t in hyp_window] )
            score = jiwer.cer(
                filter_out(sentence, ' '),
                filter_out(hyp_sentence, ' ')
                )

            if score >= 0.5 or score == 0.0:
                matches.append( {"score": score, "span": span, "hyp": hyp_sentence} )
                continue
            
            # Try to find a local minima for the CER by looking back
            # or further down, one word at a time
            max_left_score = score
            max_left_hyp_sentence = ""
            off = 1
            while i+l-off > i:
                hyp_window = hyp[i: i+l-off]
                hyp_sentence_left = ' '.join( [t["word"].lower().replace('-', ' ') for t in hyp_window] )
                left_score = jiwer.cer(
                    filter_out(sentence, ' '),
                    filter_out(hyp_sentence_left, ' ')
                    )
                if left_score < max_left_score:
                    max_left_score = left_score
                    max_left_span = (i, i+l-off)
                    max_left_hyp_sentence = hyp_sentence_left
                else:
                    break
                off += 1
            
            max_right_score = score
            max_right_hyp_sentence = ""
            off = 1
            while i+l+off < len(hyp):
                hyp_window = hyp[i: i+l+off]
                hyp_sentence_right = ' '.join( [t["word"].lower().replace('-', ' ') for t in hyp_window] )
                right_score = jiwer.cer(
                    filter_out(sentence, ' '),
                    filter_out(hyp_sentence_right, ' ')
                    )
                if right_score < max_right_score:
                    max_right_score = right_score
                    max_right_span = (i, i+l+off)
                    max_right_hyp_sentence = hyp_sentence_right
                else:
                    break
                off += 1

            if max_left_score < score:
                if max_left_score < max_right_score:
                    matches.append( {"score": max_left_score, "span": max_left_span, "hyp": max_left_hyp_sentence} )
                else:
                    matches.append( {"score": max_right_score, "span": max_right_span, "hyp": max_right_hyp_sentence} )
            else:
                if max_right_score < score:
                    matches.append( {"score": max_right_score, "span": max_right_span, "hyp": max_right_hyp_sentence} )
                else:
                    matches.append( {"score": score, "span": span, "hyp": hyp_sentence} )
        
        matches.sort(key=lambda x: x["score"])
        line_matches.append(matches)

    # Try to repair broken segments
    # last_t = 0
    # for i in range(len(cleaned_lines)):
    #     match = line_matches[i][0]
    #     if match["span"][0] < last_t:
    #         new_span = (line_matches[i-2][0]["span"][1]+1, match["span"][0])
    #         hyp_window = hyp[new_span[0]: new_span[1]]
    #         hyp_sentence = ' '.join( [t["word"].lower() for t in hyp_window] )
    #         line_matches[i-1] = [{"span": new_span, "score": 999, "hyp": hyp_sentence}]
    #     # elif i>0 and match["span"][0] == last_t:
    #     #     new_span = (match["span"][0] + 0.05, match["span"][1])
    #     #     line_matches[i] = [{"span": new_span, "score": match["score"]}]
    #     #     prev = line_matches[i-1][0]
    #     #     new_span = (prev["span"][0], prev["span"][1] - 0.05)
    #     #     line_matches[i-1] = [{"span": new_span, "score": prev["score"]}]
    #     last_t = match["span"][1]
            

    if args.type == "srt":
        subs = []
        last = -1
        for i, line in enumerate(lines):
            span = line_matches[i][0]["span"]
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

            # print(f"{start}:{end}\t{line.strip()}\t{' '.join( [ w['word'] for w in hyp[span[0]:span[1]] ] )}")

        print(srt.compose(subs))
    
    if args.type == "split":
        utts = []
        for i, line in enumerate(lines):
            span = line_matches[i][0]["span"]
            start = int(hyp[span[0]]["start"] * 1000)
            end = int(hyp[span[1]-1]["end"] * 1000)
            print(f"{start} {end}")

    for i, l in enumerate(cleaned_lines):
        print(i, l)
        hyp_sentence = line_matches[i][0]["hyp"]
        # print(f"  {hyp_sentence} ({line_matches[i][0]['score']})")
        print(line_matches[i][0])
    
    # print(' '.join([ t["word"] for t in hyp] ))