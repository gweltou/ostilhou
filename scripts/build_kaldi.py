#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Build necessary files to train a model with Kaldi toolkit
All generated files are written in the `data` directory

Usage : ./build_kaldi_files.py -h

Author:  Gweltaz Duval-Guennoc


Workflow details:

"""


import sys
import os
import argparse
from colorama import Fore
from math import floor, ceil

from ostilhou import normalize_sentence
from ostilhou.text import (
    filter_out_chars, filter_in_chars,
    pre_process,
    PUNCTUATION, LETTERS
)
from ostilhou.asr import (
    phonemes,
    special_tokens,
    phonetize_word,
    parse_dataset,
)
from ostilhou.dicts import stopwords
from ostilhou.utils import sec2hms, list_files_with_extension, read_file_drop_comments
from ostilhou.audio import export_segment, convert_to_wav, is_audiofile_valid_format



def clean_filename(filename: str) -> str:
    """ Convert a regular filename to a Kaldi friendly filename """
    filename = filename.replace(' ', '_')
    filename = filter_in_chars(filename, LETTERS + LETTERS.upper() + "0123456789_-")
    return filename



##############################################################################
###################################  MAIN  ###################################
##############################################################################


if __name__ == "__main__":
    desc = "Generate Kaldi training files"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--train", help="train dataset directory", required=True)
    parser.add_argument("--test", help="train dataset directory")
    parser.add_argument("--lm-corpus", nargs='+', help="path to one or more text files to build the language model")
    parser.add_argument("-n", "--no-lm", help="do not copy utterances to language model", action="store_true")
    parser.add_argument("-d", "--dry-run", help="run script without actualy writting files to disk", action="store_true")
    parser.add_argument("--draw-figure", help="draw a pie chart showing data repartition", action="store_true")
    parser.add_argument("-v", "--verbose", help="display errors and warnings", action="store_true")
    parser.add_argument("-o", "--output", help="Output folder for generated Kalid files", default="data")
    parser.add_argument("--lm-min-token", help="Minimum number of tokens in sentence for adding it to LM corpus", type=int, default=3)
    parser.add_argument("--utt-min-len", help="Minimum length of audio utterances", type=float, default=0.0)
    parser.add_argument("--hash-id", help="Hash speaker ids", action="store_true")
    parser.add_argument("--exclude", help="filepath containing a list of data files to exclude from training", type=str)
    parser.add_argument("--split-audio", help="Split audio files by segments", action="store_true")
    args = parser.parse_args()
    print(args)

    if not os.path.isdir(args.train):
        raise NotADirectoryError("`train` argument should be a directory containing aligned data")
    if args.test and not os.path.isdir(args.test):
        raise NotADirectoryError("`test` argument should be a directory containing aligned data")
    
    speakers_gender = {"unknown": "u"}

    # Exclude specific files from training data
    exclude = []
    if args.exclude:
        with open(args.exclude, 'r', encoding='utf-8') as _f:
            exclude.extend([l.strip() for l in _f.readlines()])
    
    stopwords = { word.lower() for word in stopwords }
        
    print("\n==== PARSING DATA ITEMS ====")
    corpora = { "train": parse_dataset(args.train, exclude, args) }
    if args.test: corpora["test"] = parse_dataset(args.test, exclude, args)


    if not os.path.exists(args.output):
        os.mkdir(args.output)

    dir_kaldi_local = os.path.join(args.output, "local")
    if not os.path.exists(dir_kaldi_local):
        os.mkdir(dir_kaldi_local)
    
    audio_dir = os.path.abspath(os.path.join(args.output, "converted"))
    if not os.path.exists(audio_dir):
        os.mkdir(audio_dir)
        

    print("\n==== BUILDING KALDI FILES ====")
    # Copy text from train utterances to language model corpus
    print(f"building file \'{os.path.join(dir_kaldi_local, 'corpus.txt')}\'")
    with open(os.path.join(dir_kaldi_local, "corpus.txt"), 'w', encoding='utf-8') as fout:
        n = 0
        for l in corpora["train"]["corpus"]:
            fout.write(f"{l}\n")
            n += 1
        print(f" {n} sentences added")
    
    # External text corpora will be added now
    if args.lm_corpus:
        print("parsing external corpora :")
        corpus_files = []
        for file in args.lm_corpus:
            if os.path.isdir(file):
                # Expand directory
                corpus_files.extend(list_files_with_extension(['txt', 'cor'], file))
            else:
                corpus_files.append(file)
                    
        with open(os.path.join(dir_kaldi_local, "corpus.txt"), 'a', encoding='utf-8') as fout:
            # for text_file in list_files_with_extension(".txt", LM_TEXT_CORPUS_DIR):
            for file in corpus_files:
                print(Fore.GREEN + f" * {file}" + Fore.RESET)
                n = 0
                for line in read_file_drop_comments(file):
                    sentence = line
                    cleaned = pre_process(sentence)
                    cleaned = normalize_sentence(cleaned.strip(), autocorrect=True, norm_case=True)
                    cleaned = cleaned.replace('-', ' ').replace('/', ' ')
                    cleaned = cleaned.replace('\xa0', ' ')
                    cleaned = filter_out_chars(cleaned, PUNCTUATION+'{}*')
                    for word in cleaned.split():
                        if word in corpora["train"]["lexicon"]:
                            pass
                        elif word == "'":
                            pass
                        elif '·' in word: # Don't add inclusive words for now
                            pass
                        else:
                            corpora["train"]["lexicon"].add(word)
                    fout.write(' '.join(cleaned.split()) + '\n') # Remove multi-spaces
                    n += 1
                print(f" {n} sentences added")
        
    
    dir_dict_nosp = os.path.join(dir_kaldi_local, 'dict_nosp')
    if not os.path.exists(dir_dict_nosp):
        os.mkdir(dir_dict_nosp)
    
    # Lexicon.txt
    lexicon_path = os.path.join(dir_dict_nosp, 'lexicon.txt')
    print(f"building file \'{lexicon_path}\'")

    if "test" in corpora:
        corpora["train"]["lexicon"].update(corpora["test"]["lexicon"])

    with open(lexicon_path, 'w', encoding='utf-8') as f_out:
        f_out.write("!SIL SIL\n"
                    "<SPOKEN_NOISE> SPN\n"
                    "<UNK> SPN\n"
                    "<C'HOARZH> LAU\n"
                    "<NTT> SPN\n"
                    "<HUM> SPN\n"
                    "<PASAAT> SPN\n"
                    "<FRONAL> SPN\n"
                    "<SONEREZH> NSN\n")
        for word in sorted(corpora["train"]["lexicon"]):
            if word.lower() in stopwords:
                continue
            prons, errors = phonetize_word(word)
            for pron in prons:
                if not pron:
                    print(Fore.RED + "ERROR empty pronunciation" + Fore.RESET, word)
                elif errors == 0:
                    f_out.write(f"{word} {pron}\n")
    
    # silence_phones.txt
    silence_phones_path  = os.path.join(dir_dict_nosp, "silence_phones.txt")
    print(f"building file \'{silence_phones_path}\'")
    with open(silence_phones_path, 'w', encoding='utf-8') as f:
        f.write(f'SIL\noov\nSPN\nLAU\nNSN\n')
    
    # nonsilence_phones.txt
    nonsilence_phones_path = os.path.join(dir_dict_nosp, "nonsilence_phones.txt")
    print(f"building file \'{nonsilence_phones_path}\'")
    with open(nonsilence_phones_path, 'w', encoding='utf-8') as f:
        for p in sorted(phonemes):
            f.write(f'{p}\n')
    
    # optional_silence.txt
    optional_silence_path  = os.path.join(dir_dict_nosp, "optional_silence.txt")
    print(f"building file \'{optional_silence_path}\'")
    with open(optional_silence_path, 'w', encoding='utf-8') as f:
        f.write('SIL\n')


    for corpus_name in corpora:
        corpus = corpora[corpus_name]
        save_dir = os.path.join(args.output, corpus_name)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        
        # Convert audio files in wavscp to 16KHz 16bit mono PCM format
        print("Converting audio files to 16KHz s16le PCM, if necessary...")
        new_wavscp = []
        for rec_id, audio_path in corpus["wavscp"]:
            _, filename = os.path.split(audio_path)
            if not is_audiofile_valid_format(audio_path) or ' ' in filename:
                # Kaldi doesn't like whitespaces in file path
                basename, audio_format = os.path.splitext(filename)
                basename = clean_filename(basename)
                converted_path = os.path.join(audio_dir, basename + ".wav")
                if not args.dry_run and not os.path.exists(converted_path):
                    convert_to_wav(audio_path, converted_path, verbose=True)
                audio_path = converted_path
            new_wavscp.append((rec_id, audio_path))
        corpus["wavscp"] = new_wavscp

        if args.split_audio:
            # Split audio files to individual segments
            # wavscp data must be changed from 'rec_id' -> 'audio_path'
            # to 'utt_id' -> 'audio-path'
            print("Splitting audio files...")
            new_wavscp = []
            for rec_id, audio_path in corpus["wavscp"]:
                print(" *", audio_path, flush=True)
                for utt_id, seg_rec_id, start, end in corpus["segments"]:
                    # Find all segments corresponding to this rec_id
                    if seg_rec_id == rec_id:
                        output_file = f"{rec_id}_{floor(start*100):0>7}-{ceil(end*100):0>7}.wav"
                        output_file = os.path.join(audio_dir, output_file)
                        if not os.path.exists(output_file):
                            export_segment(audio_path, start, end, output_file)
                        new_wavscp.append((utt_id, output_file))
                # Remove original audio file if it was already in audio dir
                if os.path.split(audio_path)[0] == audio_dir:
                    os.remove(converted_path)
            corpus["wavscp"] = new_wavscp

        # Build 'text' file
        fname = os.path.join(save_dir, 'text')
        print(f"Building file \'{fname}\'")
        with open(fname, 'w', encoding='utf-8') as f:
            for utt_id, sentence in corpus["text"]:
                f.write(f"{utt_id}\t{sentence}\n")
        
        # Build 'segments' file (optional)
        # start and end are measured in seconds
        if not args.split_audio:
            fname = os.path.join(save_dir, 'segments')
            print(f"Building file \'{fname}\'")
            with open(fname, 'w', encoding='utf-8') as f:
                for utt_id, rec_id, start, end in corpus["segments"]:
                    f.write(f"{utt_id}\t{rec_id}\t{start}\t{end}\n")
        
        # Build 'utt2spk'
        fname = os.path.join(save_dir, 'utt2spk')
        print(f"Building file \'{fname}\'")
        with open(fname, 'w', encoding='utf-8') as f:
            for utt_id, speaker_id in sorted(corpus["utt2spk"]):
                f.write(f"{utt_id}\t{speaker_id}\n")
        
        # Build 'spk2gender'
        fname = os.path.join(save_dir, 'spk2gender')
        print(f"Building file \'{fname}\'")
        with open(fname, 'w', encoding='utf-8') as f:
            for speaker in sorted(corpus["speakers"]):
                if speaker not in speakers_gender: continue
                f.write(f"{speaker}\t{speakers_gender[speaker]}\n")
        
        # Build 'wav.scp'
        fname = os.path.join(save_dir, 'wav.scp')
        print(f"Building file \'{fname}\'")
        with open(fname, 'w', encoding='utf-8') as f:
            for rec_id, audio_path in sorted(corpus["wavscp"]):
                f.write(f"{rec_id}\t{audio_path}\n")
        
    
    print("\n==== STATS ====")

    for corpus_name in corpora:
        corpus = corpora[corpus_name]
        print(f"== {corpus_name.capitalize()} ==")
        print(f"- {len(corpus['text'])} utterances")
        audio_length_m = corpus["audio_length"]['m']
        audio_length_f = corpus["audio_length"]['f']
        audio_length_u = corpus["audio_length"]['u']
        total_audio_length = audio_length_f + audio_length_m + audio_length_u
        print(f"- Total audio length:\t{sec2hms(total_audio_length)}")
        print(f"- Male speakers:\t{sec2hms(audio_length_m)}\t{audio_length_m/total_audio_length:.1%}")
        print(f"- Female speakers:\t{sec2hms(audio_length_f)}\t{audio_length_f/total_audio_length:.1%}")
        if audio_length_u > 0:
            print(f"- Unknown speakers:\t{sec2hms(audio_length_u)}\t{audio_length_u/total_audio_length:.1%}")

    print(f"\nLexicon: {len(corpora['train']['lexicon'])} words")



    if args.draw_figure:
        import matplotlib.pyplot as plt
        import datetime

        plt.figure(figsize = (8, 8))

        total_audio_length = corpora["train"]["audio_length"]["f"] \
            + corpora["train"]["audio_length"]["m"] \
            + corpora["train"]["audio_length"]["u"]
        keys, val = zip(*corpora["train"]["subdir_audiolen"].items())
        keys = [ k.replace('_', ' ') if v/total_audio_length>0.02 else ''
                 for k,v in corpora["train"]["subdir_audiolen"].items() ]
        
        def labelfn(pct):
            if pct > 2:
                return f"{sec2hms(total_audio_length*pct/100)}"
        plt.pie(val, labels=keys, normalize=True, autopct=labelfn)
        plt.title(f"Dasparzh ar roadennoù, {sec2hms(total_audio_length)} en holl")
        plt.savefig(os.path.join(args.output, f"subset_division_{datetime.datetime.now().strftime('%Y-%m-%d')}.png"))
        print(f"\nFigure saved to \'{os.path.abspath(args.output)}\'")
        # plt.show()