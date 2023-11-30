#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
    Create a split file (time segments) from an audio file
    Convert audio file to correct format (wav mono 16kHz) if needed
    UI to listen and align audio segments with sentences in text file
    
    Author: Gweltaz Duval-Guennoc

    Bugs:
        - Automatic translation gets stuck when given an 'eaf' file as argument
"""


import os
import argparse
import re
from math import floor, ceil
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from pydub.playback import _play_with_simpleaudio
from pyrubberband import time_stretch

from ostilhou.utils import splitToEafFile, eafToSplitFile
from ostilhou.asr import load_vosk, load_text_data, load_segments_data, transcribe_segment
from ostilhou.hspell import get_hspell_mistakes
from ostilhou.text import pre_process, normalize_sentence, strip_punct
from ostilhou.dicts import acronyms
from ostilhou.audio import get_audiofile_info, convert_to_wav, split_to_segments



ACRONYM_PATH = "/home/gweltaz/Documents/STT/ostilhoù/ostilhou/dicts/acronyms.tsv"

RESIZE_PATTERN = re.compile(r"([s|e])([-|\+])(\d+)")
SPLIT_PATTERN = re.compile(r"c([0-9\.]+)")

textfile_header = \
"""{source: }
{source-audio: }
{author: }
{licence: }
{tags: }\n\n\n\n\n\n
"""

play_process = None



def play_segment_text(idx, song, segments, utterances, speed):
    global play_process
    if play_process and play_process.is_playing():
        play_process.stop()
    
    if idx < len(utterances):
        sent = pre_process(utterances[idx][0])
        sent = normalize_sentence(sent)
        correction, _ = get_hspell_mistakes(sent)
        print(f'{{{utterances[idx][1].get("speaker", "unkwnown")}}} {correction}')
    seg = song[segments[idx][0]:segments[idx][1]]
    if speed != 1.0:
        y = np.array(seg.get_array_of_samples())
        y = time_stretch(y, seg.frame_rate, speed)
        y = np.int16(y * 2**15)
        seg = AudioSegment(y.tobytes(), frame_rate=seg.frame_rate, sample_width=2, channels=1)
    play_process = _play_with_simpleaudio(seg)
    #play_segment(idx, song, segments, speed)



def save_segments(segments, filename):
    with open(filename, 'w') as f:
        for _, s in enumerate(segments):
            start = int(s[0])
            stop =  int(s[1])
            f.write(f"{start} {stop}\n")
    print('split file saved')


def is_acronym(word):
    if len(word) == 1 and word in "BCDFGHIJKLPQRSTVXYZ":
        return True

    if len(word) < 2:
        return False
    
    valid = False
    for l in word:
        if l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            valid = True
            continue
        if l not in "-0123456789":
            return False
    return valid


def extract_acronyms(text):
    return  #TODO

    extracted = set()
    #for w in tokenize(text, post_proc=False):
    for w in text.split():
        w = strip_punct(w)
        # Remove black-listed words (beggining with '*')
        if w.startswith('*'):
            continue
        if is_acronym(w):
            extracted.add(w)
    
    return list(extracted)


def prompt_acronym_phon(w, song, segments, idx):
    """
        w: Acronym
        i: segment number in audiofile (from 'split' file) 
    """
    
    return  #TODO

    guess = ' '.join([acr2f[l] for l in w if l in acr2f])
    print(f"Phonetic proposition for '{w}' : {guess}")
    while True:
        answer = input("Press 'y' to validate, 'l' to listen, 'x' to skip or write a different prononciation: ").strip().upper()
        if not answer:
            continue
        if answer == 'X':
            return None
        if answer == 'Y':
            return guess
        if answer == 'L':
            play_segment(idx, song, segments, 1.5)
            continue
        valid = True
        for phoneme in answer.split():
            if phoneme not in phonemes:
                print("Error : phoneme not in", ' '.join(phonemes))
                valid = False
        if valid :
            return answer


# def split_segments(song: AudioSegment, min_silence_len, silence_thresh):
    
#     segments = detect_nonsilent(song, min_silence_len, silence_thresh)
    
#     # Including silences at head and tail of segments
#     if len(segments) >= 2:
#         segments[0] = (segments[0][0], segments[0][1] + args.dur)
#         segments[-1] = (segments[-1][0] - args.dur, segments[-1][1])
#         for i in range(1, len(segments)-1):
#             segments[i] = (segments[i][0] - args.dur, segments[i][1] + args.dur)
    
#     return segments



def main():
    parser = argparse.ArgumentParser(
                    prog = 'Wavsplit',
                    description = 'Audio file converter, splitter and text alignment')
    parser.add_argument('filename')
    # parser.add_argument('-o', '--overwrite', action='store_true', help="Overwrite split file (if present)")
    # parser.add_argument('-t', '--thresh', type=float, default=-62, metavar="DB", help="Silence intensity threshold (in decibels)")
    # parser.add_argument('-d', '--dur', type=int, default=400, metavar="MS", help="Silence minimum duration (in millisecs)")
    parser.add_argument('-s', '--transcribe', action='store_true', help="Automatic transcription")
    parser.add_argument("-m", "--model", help="Vosk model to use for decoding", metavar='MODEL_PATH')
    parser.add_argument('--keep-sil', action='store_true', help="Keep silent utterances")

    args = parser.parse_args()
    print(args)

    if args.filename.endswith(".eaf"):
        eafToSplitFile(args.filename)

    # PLAYER = get_player_name()
    
    rep, filename = os.path.split(os.path.abspath(args.filename))
    # Removing special characters from filename
    recording_id = '_'.join(filename.split(os.path.extsep)[:-1])
    recording_id = recording_id.replace('&', '_')
    recording_id = recording_id.replace(' ', '_')
    #recording_id = recording_id.replace('.', '_')
    recording_id = recording_id.replace("'", '')
    recording_id = recording_id.replace(",", '')
    print(recording_id)
    
    wav_filename = os.path.join(rep, os.path.extsep.join((recording_id, 'wav')))
    split_filename = os.path.join(rep, os.path.extsep.join((recording_id, 'split')))
    text_filename = os.path.join(rep, os.path.extsep.join((recording_id, 'txt')))

    # Converting sound file to 16kHz mono wav if needed
    if args.filename.endswith('.wav'):
        fileinfo = get_audiofile_info(args.filename)
        if fileinfo["channels"] != 1 \
            or fileinfo["sample_rate"] != "16000" \
            or fileinfo["bits_per_sample"] != 16:

            convert_to_wav(args.filename, wav_filename)
    else:
        # Audio file is not PCM
        convert_to_wav(args.filename, wav_filename)
    
    song = AudioSegment.from_wav(wav_filename)

    segments = []
    do_split = True

    if os.path.exists(split_filename):
        print("Split file already exists.")
        segments = load_segments_data(split_filename)
        do_split = False


    if do_split:
        print("spliting wave file")
        segments = split_to_segments(song, max_length=20, min_length=2)
        save_segments(segments, split_filename)
    

    if args.transcribe:
        print("Automatic transcription")
        do_transcribe = True
        if os.path.exists(text_filename):
            print("Text file already exists.")
            while True:
                a = input("Overwrite (y/n)? ")
                if a == 'y':
                    break
                if a == 'n':
                    do_transcribe = False
                    break
        if do_transcribe:
            if args.model:
                load_vosk(args.model)
            
            print("Transcribing...")
            t_min, t_max = 0, segments[-1][1]
            print(segments)
            sentences = [
            	transcribe_segment(song[max(t_min, seg[0]-200):min(t_max, seg[1]+200)]) for seg in segments
            	]
            if not args.keep_sil:
                print("Deleting silent utterances...")
                seg_keepers = []
                sent_keepers = []
                for i, seg in enumerate(segments):
                    if sentences[i] not in ('-', ''):
                        seg_keepers.append(seg)
                        sent_keepers.append(sentences[i])
                segments = seg_keepers
                sentences = sent_keepers
                save_segments(segments, split_filename)
                
            with open(text_filename, 'w') as fw:
                fw.write(textfile_header)  # Text file split_header
                for s in sentences: fw.write(f"{s if s else '-'}\n")
    else:
        # Create empty text file if it doesn't exist
        if not os.path.exists(text_filename):
            with open(text_filename, 'w') as fw:
                fw.write(textfile_header)  # Text file split_header
    utterances = load_text_data(text_filename)


    short_utterances = []
    total_length = 0
    smallest_seg = (None, 9999)
    longest_seg = (None, 0)
    for i, (start, stop) in enumerate(segments):
        l = (stop-start)/1000.0
        if l < smallest_seg[1]:
            smallest_seg = (i+1, l)
        if l > longest_seg[1]:
            longest_seg = (i+1, l)
        total_length += l
        if l < 1.3:
            short_utterances.append(i+1)
    minute, sec = divmod(round(total_length), 60)
    print(f"Segments total length: {minute}'{sec}\"")
    print(f"Shortest segment: {smallest_seg[1]}s [{smallest_seg[0]}], longest segment: {longest_seg[1]}s [{longest_seg[0]}]")
    if short_utterances:
        print("Short utterances:", short_utterances)
    
    
    running = True
    idx = 0
    speed = 1
    modified = False
    segments_undo = []
    textfile_mtime = os.path.getmtime(text_filename)
    while running:
        start, stop = segments[idx]
        length = round((stop - start) / 1000.0, 1)
        x = input(f"{'*' if modified else ''}{idx+1}/{len(segments)} [{round(start/1000.0,1)}:{round(stop/1000.0,1)}] {length}s> ").strip()
        resize_match = RESIZE_PATTERN.match(x)
        split_match = SPLIT_PATTERN.match(x)
        
        # Reload text file if it's been modified
        mtime = os.path.getmtime(text_filename)
        if mtime > textfile_mtime:
            utterances = load_text_data(text_filename)     
        if resize_match:
            segments_undo = segments[:]
            pos = resize_match.groups()[0]
            delay = int(resize_match.groups()[1] + resize_match.groups()[2])
            if pos == 's':
                segments[idx] = (start + delay, stop)
            elif pos == 'e':
                segments[idx] = (start, stop + delay)
            modified = True
        elif split_match:
            segments_undo = segments[:]
            pc = float(split_match.groups()[0])
            cut = start + (stop-start) * pc/100.0
            segments = segments[:idx] + [(start, ceil(cut)), (floor(cut), stop)] + segments[idx+1:]
            modified = True
            print(f"Segment split at {pc}% of its length")
        elif x.startswith('cc'): # Automatic split
            segments_undo = segments[:]
            seg = song[segments[idx][0]:segments[idx][1]]
            # if split_header:
            split_args = x.split()
            new_args = parser.parse_args(split_args)
            #new_args.thresh = min(new_args.thresh, args.thresh)
            print(new_args)
            subsegments = detect_nonsilent(seg, min_silence_len=new_args.dur, silence_thresh=new_args.thresh)
            if len(subsegments) > 1:
                subsegments = [(s + start, e + start) for s, e in subsegments]
                segments = segments[:idx] + subsegments + segments[idx+1:]
                modified = True
            else:
                print("No subsegments found...")
        elif x == 'r':
            play_segment_text(max(0, idx), song, segments, utterances, speed)
        elif x.isnumeric():
            idx = (int(x)-1) % len(segments)
            play_segment_text(idx, song, segments, utterances, speed)
        elif x == '+' or x == 'n':
            idx = (idx+1) % len(segments)
            play_segment_text(idx, song, segments, utterances, speed)
        elif x.startswith('+') and x[1:].isdigit():
            n = int(x[1:])
            idx = (idx+n) % len(segments)
            play_segment_text(idx, song, segments, utterances, speed)
        elif x == '-' or x == 'p':
            idx = (idx-1) % len(segments)
            play_segment_text(idx, song, segments, utterances, speed)
        elif x.startswith('-') and x[1:].isdigit():
            n = int(x[1:])
            idx = (idx-n) % len(segments)
            play_segment_text(idx, song, segments, utterances, speed)
        elif x == '*':
            speed *= 1.15
            print("speed=", speed)
        elif x == '/':
            speed *= 0.9
            print("speed=", speed)
        elif x == 'd':  # Delete segment
            segments_undo = segments[:]
            if play_process and play_process.is_playing():
                play_process.stop()
            del segments[idx]
            idx = max(0, idx-1)
            modified = True
            print("segment deleted")
        elif x == 'j' and idx > 0:  # Join this segment with previous segment
            segments_undo = segments[:]
            start = segments[idx-1][0]
            stop = segments[idx][1]
            del segments[idx]
            idx = max(0, idx-1)
            segments[idx] = (start, stop)
            modified = True
            print("segments joined")
        elif x == 'a':  # Acronym extraction
            for acr in extract_acronyms(utterances[idx][0]):
                add_pron = ""
                if acr in acronyms:
                    while not add_pron in ('a', 'k'):
                        add_pron = input(f"{acr} already known [{acronyms[acr]}], keep/add ? ('k', 'a') ").strip().lower()
                    if add_pron == 'k': continue
                    
                phon = prompt_acronym_phon(acr, song, segments, idx)
                if phon:
                    if add_pron == 'a':
                        acronyms[acr].append(phon)
                    else: acronyms[acr] = [phon]
                    with open(ACRONYM_PATH, 'a') as f:
                            f.write(f"{acr} {phon}\n")
        elif x == 't':  # Transcribe with vosk
            seg = song[segments[idx][0]:segments[idx][1]]
            print(transcribe_segment(seg))
        elif x == 'z' and segments_undo:  # Undo
            print("Undone")
            segments = segments_undo
            modified = True
        elif x == 'm': # Show metadata
            print(utterances[idx][1])
        elif x == 'x' or x == 'e':  # Export segment
            seg = song[segments[idx][0]:segments[idx][1]]
            seg_name = os.path.join(rep, os.path.extsep.join((recording_id + f"_seg{idx:03d}", 'wav')))
            seg.export(seg_name, format="wav")
            print("Segment exported")
        elif x == 's':  # Save split data to disk
            if modified:
                save_segments(segments, split_filename)
                modified = False
        elif x == 'eaf': # Export to Elan format
            splitToEafFile(split_filename)
            print('EAF file saved')
        elif x == 'h' or x == '?':  # Help
            print("Press <Enter> to play or stop current segment")
            print("'r'\t\tRepeat current segment")
            print("'+' or 'n'\tGo to next segment and play")
            print("'-' or 'p'\tGo back to previous segment and play")
            print("'-[n]' or '+[n]'\tGo backward/forward n positions")
            print("'*'\t\tSpeed playback up")
            print("'/'\t\tSlow playback down")
            print("'d'\t\tDelete current segment")
            print("'j'\t\tJoin current segment with previous one")
            print("[s/e][+/-]millisecs\tedit segment (ex: e+500, add 500ms to end)")
            print("'c[PC]'\t\tsplit current segment at PC percent of its length (ex: c66.6)")
            print("'z'\t\tUndo previous segment modification")
            print("'a'\t\tRegister acronym")
            print("'t'\t\tAutomatic transcription")
            print("'m'\t\tShow metadata")
            print("'s'\t\tSave")
            print("'x/e'\t\tExport audio segment")
            print("'eaf'\t\tExport to Elan format (.eaf)")
            print("'q'\t\tQuit")
            print("'h' or '?'\t\tShow this help")
        elif not x:
            # Play / Stop playback
            if play_process and play_process.is_playing():
                play_process.stop()
            else:
                play_segment_text(max(0, idx), song, segments, utterances, speed)
        elif x == 'q':
            if modified:
                r = input("Save before quitting (y|n) ? ")
                if r != 'n': save_segments(segments, split_filename) 
            running = False


if __name__ == "__main__":
    main()
