#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
    File: build_tsv.py

    Build a tsv file from a folder hierarchy or a single alignment file.
    Split audio files in as many utterances.

    Usage : python3 build_dataset.py --train file.seg -o output_dir

    Author:  Gweltaz Duval-Guennoc (2023)
"""


import sys
import os
import argparse
import json
from hashlib import md5
from colorama import Fore
from uuid import uuid4

from ostilhou import normalize_sentence
from ostilhou.text import (
    pre_process,
    normalize_sentence,
    filter_out_chars,
    PUNCTUATION,
    VALID_CHARS,
)
from ostilhou.asr import (
    load_segments_data,
    load_text_data,
    load_ali_file,
)
from ostilhou.audio import load_audiofile
from ostilhou.utils import sec2hms, green, yellow, red



utt_ids = set()
speakers_gender = {"unknown": "u"}
n_dropped = 0

valid_chars = set(VALID_CHARS)


def parse_dataset(file_or_dir):
    file_ext = os.path.splitext(file_or_dir)[1]
    if file_ext in (".split", ".seg", ".ali"):   # Single data item
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
            file_ext = os.path.splitext(filename)[1]
            if os.path.isdir(os.path.join(file_or_dir, filename)) \
                    or file_ext in (".split", ".seg", ".ali"):
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



def parse_data_file(filepath):
    global n_dropped

    # basename = os.path.basename(split_filename).split(os.path.extsep)[0]
    # print(Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET)
    seg_ext = os.path.splitext(filepath)[1]
    audio_path = ""

    if seg_ext == ".ali":
        ali_data = load_ali_file(filepath)
        segments = ali_data["segments"]
        text_data = list(zip(ali_data["sentences"], ali_data["metadata"]))
        audio_path = ali_data["audio_path"]
    else: # .seg, .split
        text_filename = filepath.replace(seg_ext, '.txt')
        assert os.path.exists(text_filename), f"ERROR: no text file found for {filepath}"
        segments = load_segments_data(filepath)
        text_data = load_text_data(text_filename)

    if not audio_path:
        audio_path = os.path.abspath(filepath.replace(seg_ext, '.wav'))
        if not os.path.exists(audio_path):
            audio_path = os.path.abspath(filepath.replace(seg_ext, '.mp3'))
    assert os.path.exists(audio_path), f"ERROR: no audio file found for {filepath}"

    data = {
        "utterances": [],
        "audio_length": {'m': 0, 'f': 0, 'u': 0},    # Audio length for each gender
        }
    
    assert len(text_data) == len(segments), \
        "number of utterances in text file ({}) doesn't match number of segments in split file ({})".format(
            len(text_data), len(segments)
        )
    
    for i, (start, stop) in enumerate(segments):
        sentence, metadata = text_data[i]
        if stop - start < args.utt_min_len:
            # Skip short utterances
            print(yellow("dropped (too short): ") + sentence, file=sys.stderr)
            n_dropped += 1
            continue
        
        if "accent" not in metadata:
            metadata["accent"] = "unknown"

        speaker_id = "unknown"
        if "speaker" in metadata:
            speaker_id = md5(metadata["speaker"].encode("utf-8")).hexdigest()
        
        sentence = pre_process(sentence)
        if not sentence:
            continue

        sentence = normalize_sentence(sentence, autocorrect=True, norm_punct=True, capitalize=False)
        sentence = sentence.replace('\xa0', ' ')
        if args.no_punct:
            sentence = sentence.replace('-', ' ').replace('/', ' ')
            sentence = filter_out_chars(sentence, PUNCTUATION + '*')
        sentence = ' '.join(sentence.split())
        
        # Filter out utterances with foreign chars
        chars = set(sentence)
        if not chars.issubset(valid_chars):
            print(yellow(f"dropped (foreign chars '{chars.difference(valid_chars)}'): ")
                  + sentence, file=sys.stderr)
            n_dropped += 1
            continue


        if args.unique:
            utt_id = md5((speaker_id + sentence).encode("utf-8")).hexdigest()
        else:
            utt_id = str(uuid4()).replace('-', '')
        
        if utt_id in utt_ids:
            print(yellow("dropped (recurrent): ") + sentence, file=sys.stderr)
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
            print(red("unknown gender:"), speaker_id)
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
            [sentence, speaker_id, speaker_gender, accent, audio_path, start, stop]
        )
    
    status = green(f" * {filepath[:-len(seg_ext)]}")
    if data["audio_length"]['u'] > 0:
        status += '\t' + red("unknown speaker(s)")
    print(status, file=sys.stderr)
    return data




if __name__ == "__main__":
    global args

    desc = f"Generate a CSV file from a dataset"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--train", help="Train dataset directory", required=True)
    parser.add_argument("--test", help="Test dataset directory")
    parser.add_argument("-o", "--output", help="Output folder for generated files", default="data_hf")
    parser.add_argument("--utt-min-len", help="Minimum length of an utterance", type=float, default=0.2)
    parser.add_argument("--unique", help="Remove multiple occurences of the same utterance", action="store_true")
    parser.add_argument("--no-punct", help="Remove punctuation from sentences", action="store_true")
    parser.add_argument("-f", "--format", help="metadata file format", choices=["tsv", "jsonl"], default="jsonl")
    parser.add_argument("--audio-format", help="Audio format of exported segments", choices=['wav', 'mp3'], default='mp3')
    parser.add_argument("-d", "--dry-run", help="Run script without actualy writting files to disk", action="store_true")
    parser.add_argument("--draw-figure", help="draw a pie chart showing data repartition", action="store_true")

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

    if args.format == "tsv":
        metadata_file = open(os.path.join(args.output, "metadata.tsv"), 'w', encoding='utf-8')
        metadata_file.write('\t'.join(["file_name", "text"]) + '\n')
    elif args.format == "jsonl":
        metadata_file = open(os.path.join(args.output, "metadata.jsonl"), 'w', encoding='utf-8')

    output_folder = os.path.join(args.output, "data")
    if not args.dry_run and not os.path.exists(output_folder):
        os.mkdir(output_folder)

    last_recording_id = None

    for corpus_name, data in dataset.items(): # train / test
        n_segments = 0

        corpus_folder = os.path.join(output_folder, corpus_name)
        if not args.dry_run and not os.path.exists(corpus_folder):
            os.mkdir(corpus_folder)

        # Splitting audio files
        for utterance in data["utterances"]:
            sentence, speaker_id, speaker_gender, accent = utterance[:4]
            audio_file, start, end = utterance[4:]

            recording_id = md5(utterance[4].encode("utf8")).hexdigest()
            seg_audio_file = os.path.join("data", corpus_name, f"{recording_id}_{start:0>7}_{end:0>7}.mp3")
            
            if args.format == "tsv":
                metadata_file.write('\t'.join([seg_audio_file, sentence]) + '\n')
            elif args.format == "jsonl":
                sentence = sentence.replace('"', '\\"')
                metadata_file.write(f'{{"file_name": "{seg_audio_file}", "transcript": "{sentence}"}}\n')


            if not args.dry_run:
                if recording_id != last_recording_id:
                    print("Segmenting", os.path.split(audio_file)[1])
                    audio = load_audiofile(audio_file)
                    last_recording_id = recording_id
                
                segment = audio[start:end]
                output_file = os.path.join(corpus_folder, f"{recording_id}_{start:0>7}_{end:0>7}.{args.audio_format}")
                if not os.path.exists(output_file):
                    segment.export(output_file, format=args.audio_format)
                n_segments += 1
        

        print(f"== {corpus_name.capitalize()} ==")
        if n_segments:
            print(f"{n_segments} segments exported")

        audio_length_m = data["audio_length"]['m']
        audio_length_f = data["audio_length"]['f']
        audio_length_u = data["audio_length"]['u']
        print("\n==== STATS ====")
        total_audio_length = audio_length_f + audio_length_m + audio_length_u
        print(f"- Total audio length:\t{sec2hms(total_audio_length)}")
        print(f"- Male speakers:\t{sec2hms(audio_length_m)}\t{audio_length_m/total_audio_length:.1%}")
        print(f"- Female speakers:\t{sec2hms(audio_length_f)}\t{audio_length_f/total_audio_length:.1%}")
        if audio_length_u > 0:
            print(f"- Unknown speakers:\t{sec2hms(audio_length_u)}\t{audio_length_u/total_audio_length:.1%}")

    print(f"Files saved in {output_folder}")



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
    
    if args.draw_figure:
        import matplotlib.pyplot as plt
        import datetime

        plt.figure(figsize = (8, 8))

        total_audio_length = dataset["train"]["audio_length"]["f"] \
            + dataset["train"]["audio_length"]["m"] \
            + dataset["train"]["audio_length"]["u"]
        keys, val = zip(*dataset["train"]["subdir_audiolen"].items())
        keys = [ k.replace('_', ' ') if v/total_audio_length>0.02 else ''
                 for k,v in dataset["train"]["subdir_audiolen"].items() ]
        
        def labelfn(pct):
            if pct > 2:
                return f"{sec2hms(total_audio_length*pct/100)}"
        plt.pie(val, labels=keys, normalize=True, autopct=labelfn)
        plt.title(f"Dasparzh ar roadennoù, {sec2hms(total_audio_length)} en holl")
        plt.savefig(os.path.join(args.output, f"subset_division_{datetime.datetime.now().strftime('%Y-%m-%d')}.png"))
        print(f"\nFigure saved to \'{args.output}\'")
        # plt.show()
