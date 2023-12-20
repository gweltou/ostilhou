#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from hashlib import md5
from colorama import Fore
from uuid import uuid4

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
from ostilhou.audio import load_audiofile


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
            if os.path.isdir(os.path.join(file_or_dir, filename)) \
                    or filename.endswith(".split") \
                    or filename.endswith(".seg"):
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
    


def parse_data_file(seg_filename):
    global n_dropped

    # Kaldi doensn't like whitespaces in file path
    if ' ' in seg_filename:
        print("ERROR: whitespaces in path", seg_filename)
        sys.exit(1)
    
    # basename = os.path.basename(split_filename).split(os.path.extsep)[0]
    # print(Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET)
    seg_ext = os.path.splitext(seg_filename)[1]
    text_filename = seg_filename.replace(seg_ext, '.txt')
    assert os.path.exists(text_filename), f"ERROR: no text file found for {seg_filename}"
    wav_filename = os.path.abspath(seg_filename.replace(seg_ext, '.wav'))
    assert os.path.exists(wav_filename), f"ERROR: no wave file found for {seg_filename}"

    data = {
        "utterances": [],
        "audio_length": {'m': 0, 'f': 0, 'u': 0},    # Audio length for each gender
        }
    
    segments = load_segments_data(seg_filename)
    text_data = load_text_data(text_filename)

    assert len(text_data) == len(segments), \
        f"number of utterances in text file ({len(data['text'])}) doesn't match number of segments in split file ({len(segments)})"

    for i, (start, stop) in enumerate(segments):
        if (stop - start) / 1000 < args.utterances_min_length:
            # Skip short utterances
            continue

        sentence, metadata = text_data[i]
        if "accent" not in metadata:
            metadata["accent"] = "unknown"

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
        
        if args.unique:
            utt_id = md5((speaker_id + sentence).encode("utf-8")).hexdigest()
        else:
            utt_id = str(uuid4()).replace('-', '')
        
        if utt_id in utt_ids:
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
            data["audio_length"]['m'] += (stop - start) / 1000
        elif speaker_gender == 'f':
            data["audio_length"]['f'] += (stop - start) / 1000
        else:
            data["audio_length"]['u'] += (stop - start) / 1000

        accent = ""
        if "accent" in metadata:
            accent = metadata["accent"]
        
        data["utterances"].append(
            [sentence, speaker_id, speaker_gender, accent, wav_filename, start, stop]
        )
    
    status = Fore.GREEN + f" * {seg_filename[:-6]}" + Fore.RESET
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
    parser.add_argument("--train", help="train dataset directory", required=True)
    parser.add_argument("--test", help="train dataset directory")
    parser.add_argument("-o", "--output", help="Output folder for generated files", default="data_hf")
    parser.add_argument("--utterances-min-length", help="Minimum length of an utterance", type=float, default=0)
    parser.add_argument("--unique", help="Remove multiple occurences of the same utterance", default=True)
    parser.add_argument("-d", "--dry-run", help="run script without actualy writting files to disk", action="store_true")

    args = parser.parse_args()

    dataset = dict()
    dataset["train"] = parse_dataset(args.train)
    print("{} utterances dropped".format(n_dropped), file=sys.stderr)

    if args.test:
        n_dropped = 0
        dataset["test"] = parse_dataset(args.test)
        print("{} utterances dropped".format(n_dropped), file=sys.stderr)
    
    if not os.path.exists(args.output):
        os.mkdir(args.output)

    splitted = set()

    metadata_file = open(os.path.join(args.output, "metadata.csv"), 'w')
    metadata_file.write(','.join(["file_name", "text", "speaker_id", "gender", "accent"]) + '\n')

    wave_folder = os.path.join(args.output, "data")
    if not args.dry_run and not os.path.exists(wave_folder):
        os.mkdir(wave_folder)

    for corpus_name, data in dataset.items():
        n_segments = 0

        corpus_folder = os.path.join(wave_folder, corpus_name)
        if not args.dry_run and not os.path.exists(corpus_folder):
            os.mkdir(corpus_folder)

        for utterance in data["utterances"]:
            sentence, speaker_id, speaker_gender, accent = utterance[:4]
            audio_file, start, end = utterance[4:]

            recording_id = md5(utterance[4].encode("utf8")).hexdigest()
            seg_audio_file = os.path.join("data", corpus_name, f"{recording_id}_{start:0>7}_{end:0>7}.mp3")
            
            metadata_file.write(','.join([seg_audio_file, sentence, speaker_id, speaker_gender, accent]) + '\n')
        
            if recording_id not in splitted and not args.dry_run:
                print("Segmenting", os.path.split(audio_file)[1])
                audio = load_audiofile(audio_file)
                seg_filename = audio_file.replace(".wav", ".seg")
                if not os.path.exists(seg_filename):
                    seg_filename = audio_file.replace(".wav", ".split")
                segments = load_segments_data(seg_filename)
                for start, end in segments:
                    segment = audio[start: end]
                    output_file = os.path.join(corpus_folder, f"{recording_id}_{start:0>7}_{end:0>7}.mp3")
                    if not os.path.exists(output_file):
                        segment.export(output_file, format='mp3')
                    n_segments += 1
                splitted.add(recording_id)
        print(f"{n_segments} segments exported")


    # if args.split_audiofiles and not args.dry_run:
    #         for corpus_name, data in dataset.items():
    #             print(data.keys()   )
    #             corpus_folder = os.path.join(wave_folder, corpus_name)
    #             if not os.path.exists(corpus_folder):
    #                 os.mkdir(corpus_folder)
                
    #             for _id, wav_filename in data["wavscp"].items():
                    

    # if args.split_audiofiles:
    #     metadata_file.write("file_name, transcription" + '\n')
    #     for corpus_name, data in dataset.items():
    #         print(data["utterances"][0])
    #         print()

    # else:
        
    #     for dataset_split in dataset:
    #         for item in dataset[dataset_split]["utterances"]:
    #             print('\t'.join(map(str, item)))
    
    metadata_file.close()