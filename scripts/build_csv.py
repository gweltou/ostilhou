#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from hashlib import md5
from colorama import Fore

from ostilhou import normalize_sentence
from ostilhou.text import (
    pre_process,
    normalize_sentence,
    filter_out_chars,
    PUNCTUATION
)
from ostilhou.asr import (
    load_segments_data,
    load_text_data,
)


"""
 Build a csv file from a folder hierarcy

 Usage : ./build_csv.py -h
 
 Author:  Gweltaz Duval-Guennoc
"""


utt_ids = set()
speakers_gender = {"unknown": "u"}
n_dropped = 0


def parse_dataset(file_or_dir):
    if file_or_dir.endswith(".split") or file_or_dir.endswith(".seg"):   # Single data item
        return parse_data_file(file_or_dir)
    
    elif os.path.isdir(file_or_dir):
        data = {
            "utterances": [],
            "audio_length": {'m': 0, 'f': 0, 'u': 0},    # Audio length for each gender
            "subdir_audiolen": {}   # Size (total audio length) for every sub-folders
            }
        
        for filename in sorted(os.listdir(file_or_dir)):
            if filename.startswith('.'):
                # Skip hidden folders
                continue
            if os.path.isdir(os.path.join(file_or_dir, filename)) or filename.endswith(".split"):
                data_item = parse_dataset(os.path.join(file_or_dir, filename))
                data["utterances"].extend(data_item["utterances"])
                data["audio_length"]['f'] += data_item["audio_length"]['f']
                data["audio_length"]['m'] += data_item["audio_length"]['m']
                data["audio_length"]['u'] += data_item["audio_length"]['u']
                data["subdir_audiolen"][filename] = \
                    data_item["audio_length"]['f'] + \
                    data_item["audio_length"]['m'] + \
                    data_item["audio_length"]['u']
        
        return data
    else:
        print("File argument must be a split file or a directory")
        return
    


def parse_data_file(split_filename):
    global n_dropped

    # Kaldi doensn't like whitespaces in file path
    if ' ' in split_filename:
        print("ERROR: whitespaces in path", split_filename)
        sys.exit(1)
    
    # basename = os.path.basename(split_filename).split(os.path.extsep)[0]
    # print(Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET)
    text_filename = split_filename.replace('.split', '.txt')
    assert os.path.exists(text_filename), f"ERROR: no text file found for {split_filename}"
    wav_filename = os.path.abspath(split_filename.replace('.split', '.wav'))
    assert os.path.exists(wav_filename), f"ERROR: no wave file found for {split_filename}"

    data = {
        "utterances": [],
        "audio_length": {'m': 0, 'f': 0, 'u': 0},    # Audio length for each gender
        }
    
    segments = load_segments_data(split_filename)
    text_data = load_text_data(text_filename)

    assert len(text_data) == len(segments), \
        f"number of utterances in text file ({len(data['text'])}) doesn't match number of segments in split file ({len(segments)})"

    for i, segment in enumerate(segments):
        start = segment[0] / 1000
        stop = segment[1] / 1000
        if stop - start < args.utterances_min_length:
            # Skip short utterances
            continue

        sentence, metadata = text_data[i]

        speaker_id = "unknown"
        if "speaker" in metadata:
            speaker_id = md5(metadata["speaker"].encode("utf-8")).hexdigest()
        
        sentence = pre_process(sentence)
        if not sentence:
            continue
        sentence = normalize_sentence(sentence, autocorrect=True)
        sentence = sentence.replace('-', ' ').replace('/', ' ')
        sentence = sentence.replace('\xa0', ' ')
        sentence = filter_out_chars(sentence, PUNCTUATION)
        sentence = ' '.join(sentence.replace('*', '').split())
        
        utt_id = md5((speaker_id + sentence).encode("utf-8")).hexdigest()
        if args.unique and utt_id in utt_ids:
            print(Fore.YELLOW + "dropped (recurent): " + Fore.RESET + sentence, file=sys.stderr)
            n_dropped += 1
            continue
        utt_ids.add(utt_id)
        
        if "gender" in metadata and speaker_id != "unknown":
            if speaker_id not in speakers_gender:
                # speakers_gender is a global variable
                speakers_gender[speaker_id] = metadata["gender"]

        if speaker_id in speakers_gender:
            speaker_gender = speakers_gender[speaker_id]
        else:
            print(Fore.RED + "unknown gender:" + Fore.RESET, speaker_id)
            speaker_gender = 'u'
        
        if speaker_gender == 'm':
            data["audio_length"]['m'] += stop - start
        elif speaker_gender == 'f':
            data["audio_length"]['f'] += stop - start
        else:
            data["audio_length"]['u'] += stop - start

        accent = ""
        if "accent" in metadata:
            accent = metadata["accent"]
        
        data["utterances"].append(
            [sentence, speaker_id, speaker_gender, accent, wav_filename, int(start*1000), int(stop*1000)]
        )
    
    status = Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET
    if data["audio_length"]['u'] > 0:
        status += '\t' + Fore.RED + "unknown speaker(s)" + Fore.RESET
    print(status, file=sys.stderr)
    return data



def sec2hms(seconds):
    """ Return a string of hours, minutes, seconds from a given number of seconds """
    minutes, seconds = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}' {seconds}''"




if __name__ == "__main__":
    global args

    desc = f"Generate a CSV file from a dataset"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("path", help="dataset root directory")
    parser.add_argument("--utterances-min-length", help="Minimum length of an utterance", type=float, default=0)
    parser.add_argument("--unique", help="Remove multiple occurences of the same utterance", default=True)
    args = parser.parse_args()

    dataset = parse_dataset(args.path)
    print("{} utterances dropped".format(n_dropped), file=sys.stderr)

    sep = ','
    print(sep.join(["text", "speaker_id", "gender", "accent", "audiofile_path", "begin_time", "end_time"]))
    for item in dataset["utterances"]:
        print(sep.join(map(str, item)))
