#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create subtitles (a `srt` file) from an audio file
and a text file, using a vosk model

Author:  Gweltaz Duval-Guennoc

Usage: ./autoaligner_srt wav_file text_file

TODO :
    * tretañ ar c'hemadurioù : vMickaël, dTouène
    * Niverennoù -> stumm skrid
"""


import os
import sys
import re
import datetime
import srt
sys.path.append("../..")
from libMySTT import get_cleaned_sentence
from pydub import AudioSegment
from ostilhou.asr import load_segments_data
from ostilhou.asr.recognizer import transcribe_file_timecode
from ostilhou.text import pre_process, filter_out, PUNCTUATION
import jiwer


# KEMMADUR_PATTERN = re.compile(r" (g|b|d|w|v|c'h){1}/[a-zñ']{3,}", re.IGNORECASE)
KEMMADUR_PATTERN = re.compile(r"(vM|dT)")
"""
M -> V
T -> D
"""


if __name__ == "__main__":
    audio_filename = os.path.abspath(sys.argv[1])
    text_filename = os.path.abspath(sys.argv[2])
    
    with open(text_filename, 'r') as f:
        lines = f.readlines()
    cleaned_lines = [ filter_out(pre_process(line), PUNCTUATION + "><").strip() for line in lines ]
    cleaned_lines = [ " ".join(line.lower().replace('-', ' ').split()) for line in cleaned_lines ]

    hyp = transcribe_file_timecode(audio_filename)
    # print(hyp)

    line_matches = []

    for sentence in cleaned_lines:
        l = len(sentence.split())
        matches = []    # {"score": , "span":(s,e),}
        for i in range(len(hyp) - l):
            span = (i, i+l)
            hyp_window = hyp[i: i+l]
            # Character compare score without spaces
            score = jiwer.cer(
                filter_out(sentence, ' '),
                ''.join( [t["word"].lower() for t in hyp_window] )
                )
            
            if score >= 0.5 or score == 0.0:
                matches.append( {"score": score, "span": span} )
                continue
            
            max_left_score = score
            off = 1
            while i+l-off > i:
                hyp_window = hyp[i: i+l-off]
                left = jiwer.cer(
                    filter_out(sentence, ' '),
                    ''.join( [t["word"].lower() for t in hyp_window] )
                    )
                if left < max_left_score:
                    max_left_score = left
                    max_left_span = (i, i+l-off)
                    # print("**",
                    #     score, ' '.join( [t["word"].lower() for t in hyp[span[0]:span[1]]] ),
                    #     '||', sentence)
                    # print(left, "[left]", ' '.join( [t["word"].lower() for t in hyp_window] ))
                else:
                    break
                off += 1
            
            max_right_score = score
            off = 1
            while i+l+off < len(hyp):
                hyp_window = hyp[i: i+l+off]
                right = jiwer.cer(
                    filter_out(sentence, ' '),
                    ''.join( [t["word"].lower() for t in hyp_window] )
                    )
                if right < max_right_score:
                    max_right_score = right
                    max_right_span = (i, i+l+off)
                    # print("**",
                    #     score, ' '.join( [t["word"].lower() for t in hyp[span[0]:span[1]]] ),
                    #     '||', sentence)
                    # print(right, "[right]", ' '.join( [t["word"].lower() for t in hyp_window] ))
                else:
                    break
                off += 1

            if max_left_score < score:
                if max_left_score < max_right_score:
                    matches.append( {"score": max_left_score, "span": max_left_span} )
                else:
                    matches.append( {"score": max_right_score, "span": max_right_span} )
            else:
                if max_right_score < score:
                    matches.append( {"score": max_right_score, "span": max_right_span} )
                else:
                    matches.append( {"score": score, "span": span} )
        
        matches.sort(key=lambda x: x["score"])
        line_matches.append(matches)

    # Try to repair broken segments
    last_t = 0
    for i in range(len(cleaned_lines)):
        match = line_matches[i][0]
        if match["span"][0] < last_t:
            new_span = (line_matches[i-2][0]["span"][1]+1, match["span"][0])
            line_matches[i-1] = [{"span": new_span, "score": 999}]
        # elif i>0 and match["span"][0] == last_t:
        #     new_span = (match["span"][0] + 0.05, match["span"][1])
        #     line_matches[i] = [{"span": new_span, "score": match["score"]}]
        #     prev = line_matches[i-1][0]
        #     new_span = (prev["span"][0], prev["span"][1] - 0.05)
        #     line_matches[i-1] = [{"span": new_span, "score": prev["score"]}]
        last_t = match["span"][1]
            

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
