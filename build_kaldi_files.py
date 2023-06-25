#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
 Build necessary files to train a model with Kaldi toolkit
 All generated files are written in the `data` directory

 Usage : ./build_kaldi_files.py -h
 
 Author:  Gweltaz Duval-Guennoc
"""


import sys
import os
import argparse
import numpy as np
import re
from math import floor, ceil

from hashlib import md5
from colorama import Fore

from ostilhou import normalize_sentence
from ostilhou.text import filter_out, pre_process, split_sentences
from ostilhou.text.definitions import PUNCTUATION
from ostilhou.dicts import proper_nouns
from ostilhou.audio import add_amb_random, AUDIO_AMB_FILES
from ostilhou.asr import (
    load_segments_data,
    load_text_data,
    extract_metadata,
    lexicon_add,
    verbal_fillers,
    phonemes,
    phonetize,
)



SAVE_DIR = "data"
LM_SENTENCE_MIN_WORDS = 3 # Min number of words for a sentence to be added to the LM
UTTERANCES_MIN_LENGTH = 0 # exclude utterances shorter than this length (in seconds)



def parse_dataset(file_or_dir, args):
    if file_or_dir.endswith(".split"):   # Single data item
        return parse_data_file(file_or_dir, args)
    elif os.path.isdir(file_or_dir):
        data = {
            "path": file_or_dir,
            "wavscp": dict(),       # Wave filenames
            "utt2spk": [],      # Utterance to speakers
            "segments": [],     # Time segments
            "text": [],         # Utterances text
            "speakers": set(),  # Speakers names
            "lexicon": set(),   # Word dictionary
            "corpus": set(),    # Sentences for LM corpus
            "audio_length": {'m': 0, 'f': 0},    # Audio length for each gender
            "subdir_audiolen": {}   # Size (total audio length) for every sub-folders
            }
        
        for filename in sorted(os.listdir(file_or_dir)):
            if filename.startswith('.'):
                # Skip hidden folders
                continue
            if os.path.isdir(os.path.join(file_or_dir, filename)) or filename.endswith(".split"):
                data_item = parse_dataset(os.path.join(file_or_dir, filename), args)
                data["wavscp"].update(data_item["wavscp"])
                data["utt2spk"].extend(data_item["utt2spk"])
                data["segments"].extend(data_item["segments"])
                data["text"].extend(data_item["text"])
                data["speakers"].update(data_item["speakers"])
                data["lexicon"].update(data_item["lexicon"])
                data["corpus"].update(data_item["corpus"])
                data["audio_length"]['m'] += data_item["audio_length"]['m']
                data["audio_length"]['f'] += data_item["audio_length"]['f']
                data["subdir_audiolen"][filename] = data_item["audio_length"]['m'] + data_item["audio_length"]['f']
        
        return data
    else:
        print("File argument must be a split file or a directory")
        return
    


def parse_data_file(split_filename, args):
    # Kaldi doensn't like whitespaces in file path
    if ' ' in split_filename:
        print("ERROR: whitespaces in path", split_filename)
        sys.exit(1)
    
    # basename = os.path.basename(split_filename).split(os.path.extsep)[0]
    print(Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET)
    text_filename = split_filename.replace('.split', '.txt')
    assert os.path.exists(text_filename), f"ERROR: no text file found for {split_filename}"
    wav_filename = os.path.abspath(split_filename.replace('.split', '.wav'))
    assert os.path.exists(wav_filename), f"ERROR: no wave file found for {split_filename}"
    recording_id = md5(wav_filename.encode("utf8")).hexdigest()
    
    substitute_corpus_filename = split_filename.replace('.split', '.cor')
    replace_corpus = os.path.exists(substitute_corpus_filename)
    
    data = {
        "wavscp": {recording_id: wav_filename},   # Wave filenames
        "utt2spk": [],      # Utterance to speakers
        "segments": [],     # Time segments
        "text": [],         # Utterances text
        "speakers": set(),  # Speakers names
        "lexicon": set(),   # Word dictionary
        "corpus": set(),    # Sentences for LM corpus
        "audio_length": {'m': 0, 'f': 0},    # Audio length for each gender
        }
    
    ## PARSE TEXT FILE
    speaker_ids = []
    speaker_id = "unnamed"
    sentences = []

    for sentence, metadata in load_text_data(text_filename):
        add_to_corpus = True
        if "parser" in metadata:
            if "no-lm" in metadata["parser"]:
                add_to_corpus = False
            elif "add-lm" in metadata["parser"]:
                add_to_corpus = True
            
        if "speaker" in metadata:
            speaker_id = metadata["speaker"]
            data["speakers"].add(speaker_id)
        
        if "gender" in metadata and speaker_id != "unknown":
            if speaker_id not in speakers_gender:
                # speakers_gender is a global variable
                speakers_gender[speaker_id] = metadata["gender"]
        
        cleaned = pre_process(sentence)
        if cleaned:
            sent = normalize_sentence(cleaned, autocorrect=True)
            sent = sent.replace('-', ' ').replace('/', ' ')
            sent = filter_out(sent, PUNCTUATION)
            sentences.append(' '.join(sent.replace('*', '').split()))
            speaker_ids.append(speaker_id)
            
            # Add words to lexicon
            for word in sent.split():
                # Remove black-listed words (those beggining with '*')
                if word.startswith('*'):
                    pass
                elif word in ("<NTT>", "<C'HOARZH>", "<UNK>", "<HUM>"):
                    pass
                elif word == "'":
                    pass
                # elif word in verbal_fillers:
                #     pass
                # elif is_acronym(word):
                #     pass
                # elif word.lower() in proper_nouns:
                #     pass
                else: data["lexicon"].add(word)
        
        # Add sentence to language model corpus
        if add_to_corpus and not replace_corpus and not args.no_lm:
            for sub in split_sentences(cleaned, end=''):
                sent = normalize_sentence(sub, autocorrect=True)
                sent = sent.replace('-', ' ').replace('/', ' ')
                sent = filter_out(sent, PUNCTUATION)
                if not sent:
                    continue

                n_stared = sent.count('*')
                tokens = sent.split()
                # Ignore if to many black-listed words in sentence
                if n_stared / len(tokens) > 0.2:
                    if args.verbose:
                        print(Fore.YELLOW + "LM exclude:" + Fore.RESET, sent)
                    continue
                # Remove starred words
                tokens = [tok for tok in tokens if not tok.startswith('*')]
                # Ignore if sentence is too short
                if len(tokens) < LM_SENTENCE_MIN_WORDS:
                    if args.verbose:
                        print(Fore.YELLOW + "LM exclude:" + Fore.RESET, sent)
                    continue
                data["corpus"].add(' '.join(tokens))
    
    if replace_corpus and not args.no_lm:
        for sentence, _ in load_text_data(substitute_corpus_filename):
            for sub in split_sentences(sentence):
                sub = pre_process(sub)
                sub = normalize_sentence(sub, autocorrect=True)
                sub = sub.replace('-', ' ').replace('/', ' ')
                sub = filter_out(sub, PUNCTUATION)
                data["corpus"].add(' '.join(sub.split()))
    

    ## PARSE SPLIT FILE
    segments, _ = load_segments_data(split_filename)
    assert len(sentences) == len(segments), \
        f"number of utterances in text file ({len(data['text'])}) doesn't match number of segments in split file ({len(segments)})"

    for i, s in enumerate(segments):
        start = s[0] / 1000
        stop = s[1] / 1000
        if stop - start < UTTERANCES_MIN_LENGTH:
            # Skip short utterances
            continue

        if speaker_ids[i] in speakers_gender:
            speaker_gender = speakers_gender[speaker_ids[i]]
        else:
            print(Fore.RED + "unknown gender:" + Fore.RESET, speaker_ids[i])
            speaker_gender = 'u'
        
        if speaker_gender == 'm':
            data["audio_length"]['m'] += stop - start
        elif speaker_gender == 'f':
            data["audio_length"]['f'] += stop - start
        
        utterance_id = f"{speaker_ids[i]}-{recording_id}-{floor(100*start):0>7}_{ceil(100*stop):0>7}"
        data["text"].append((utterance_id, sentences[i]))
        data["segments"].append(f"{utterance_id}\t{recording_id}\t{floor(start*100)/100}\t{ceil(stop*100)/100}\n")
        data["utt2spk"].append(f"{utterance_id}\t{speaker_ids[i]}\n")
    
    return data



def sec2hms(seconds):
    """ Return a string of hours, minutes, seconds from a given number of seconds """
    minutes, seconds = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}' {seconds}''"




##############################################################################
###################################  MAIN  ###################################
##############################################################################


if __name__ == "__main__":
    desc = f"Generate Kaldi data files in directory '{os.path.join(os.getcwd(), SAVE_DIR)}'"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--train", help="train dataset directory", required=True)
    parser.add_argument("--test", help="train dataset directory")
    parser.add_argument("--lm-corpus", nargs='+', help="path of a text file to build the language model")
    parser.add_argument("-n", "--no-lm", help="do not copy utterances to language model", action="store_true")
    parser.add_argument("-a", "--augment", help="duplicate audio data with added noise", action="store_true")
    parser.add_argument("-d", "--dry-run", help="run script without actualy writting files to disk", action="store_true")
    parser.add_argument("-f", "--draw-figure", help="draw a pie chart showing data repartition", action="store_true")
    parser.add_argument("-v", "--verbose", help="display errors and warnings", action="store_true")
    args = parser.parse_args()
    print(args)

    if not os.path.isdir(args.train):
        print("`train` argument should be a directory containing aligned audio, text and split files")
        sys.exit(1)
    if args.test and not os.path.isdir(args.test):
        print("`test` argument should be a directory containing aligned audio, text and split files")
        sys.exit(1)
    
    speakers_gender = {}
    
    print("\n==== PARSING DATA ITEMS ====")
    corpora = { "train": parse_dataset(args.train, args) }
    if args.test: corpora["test"] = parse_dataset(args.test, args)


    ####################################
    ####     DATA AUGMENTATION      ####
    ####################################

    # if not args.dry_run and args.augment:
    #     print("TO FIX !")
    #     sys.exit(1)

    #     print("\n==== DATA AUGMENTATION ====")
    #     # If True, duplicates the whole train dataset, adding various audio noises.
    #     # The augmented data will be put in a sister folder `augmented`, with the same
    #     # directory hierarchy as the original audio corpus.

    #     root = os.path.abspath(args.train)
    #     # augmented_rep = os.path.join(os.path.abspath(SAVE_DIR), "augmented")
    #     augmented_rep = os.path.join(root, "augmented")
    #     augmented_files = dict()
        
    #     new_rec_id = dict()

    #     for (rec_id, original_audio) in corpora["train"]["wavscp"].items():
    #         recording_id = rec_id + "_AUG"
    #         utterance_id = corpora["train"]["text"][i][0]
    #         # utterance_id should not be postfixed with anything,
    #         # lest Kaldi goes back and forth between the original and augmented audio file
    #         # when extracting features for every utterance
    #         utterance_id = utterance_id.rsplit('-', maxsplit=1)
    #         utterance_id = utterance_id[0] + "_AUG_" + utterance_id[1]
    #         text = corpora["train"]["text"][i][1]
    #         corpora["train"]["text"].append((utterance_id, text))
    #         seg = corpora["train"]["segments"][i].split('\t')
    #         corpora["train"]["segments"].append(f"{utterance_id}\t{recording_id}\t{seg[2]}\t{seg[3]}")
    #         utt2spk = corpora["train"]["utt2spk"][i].split('\t')
    #         corpora["train"]["utt2spk"].append(f"{utterance_id}\t{utt2spk[1]}")

    #         rep, filename = os.path.split(original_audio)
    #         rep = rep.replace(root, augmented_rep)
    #         output_filename = os.path.join(rep, filename)
    #         augmented_files[recording_id] = output_filename
    #         if os.path.exists(output_filename):
    #             continue
    #         if not os.path.exists(rep):
    #             os.makedirs(rep)
    #         add_amb_random(original_audio, output_filename)

    #     corpora["train"]["wavscp"].update(augmented_files)
    #     print("Done.")


    if not args.dry_run:

        if not os.path.exists(SAVE_DIR):
            os.mkdir(SAVE_DIR)

        dir_kaldi_local = os.path.join(SAVE_DIR, 'local')
        if not os.path.exists(dir_kaldi_local):
            os.mkdir(dir_kaldi_local)
            

        print("\n==== BUILDING KALDI FILES ====")
        # Copy text from train utterances to language model corpus
        print(f"building file \'{os.path.join(dir_kaldi_local, 'corpus.txt')}\'")
        with open(os.path.join(dir_kaldi_local, "corpus.txt"), 'w') as fout:
            n = 0
            for l in corpora["train"]["corpus"]:
                fout.write(f"{l}\n")
                n += 1
            print(f" {n} sentences added")
        
        # External text corpus will be added now
        if args.lm_corpus:
            print("parsing and embedding external corpora :")
            with open(os.path.join(dir_kaldi_local, "corpus.txt"), 'a') as fout:
                # for text_file in list_files_with_extension(".txt", LM_TEXT_CORPUS_DIR):
                for lm_corpus_file in args.lm_corpus:
                    print(Fore.GREEN + f" * {lm_corpus_file}" + Fore.RESET)
                    n = 0
                    with open(lm_corpus_file, 'r') as fr:
                        for sentence in fr.readlines():
                            cleaned = pre_process(sentence)
                            cleaned = normalize_sentence(cleaned.strip(), autocorrect=True)
                            cleaned = cleaned.replace('-', ' ').replace('/', ' ')
                            cleaned = filter_out(cleaned, PUNCTUATION+'{}')
                            for word in cleaned.split():
                                if word in corpora["train"]["lexicon"]:
                                    pass
                                elif word == "'":
                                    pass
                                else:
                                    corpora["train"]["lexicon"].add(word)
                            fout.write(cleaned + '\n')
                            n += 1
                    print(f" {n} sentences added")
        
    
    if not args.dry_run:
        dir_dict_nosp = os.path.join(dir_kaldi_local, 'dict_nosp')
        if not os.path.exists(dir_dict_nosp):
            os.mkdir(dir_dict_nosp)
        
        # Lexicon.txt
        lexicon_path = os.path.join(dir_dict_nosp, 'lexicon.txt')
        print(f"building file \'{lexicon_path}\'")

        with open(lexicon_path, 'w') as f_out:
            f_out.write(f"!SIL SIL\n<SPOKEN_NOISE> SPN\n<UNK> SPN\n<C'HOARZH> LAU\n<NTT> SPN\n<HUM> SPN\n")
            for word in sorted(corpora["train"]["lexicon"]):
                for pron in phonetize(word):
                    if not pron:
                        print(Fore.RED + "ERROR empty pronunciation" + Fore.RESET, word)
                    # print(f"{word} {pron}\n")
                    f_out.write(f"{word} {pron}\n")
        
        # silence_phones.txt
        silence_phones_path  = os.path.join(dir_dict_nosp, "silence_phones.txt")
        print(f"building file \'{silence_phones_path}\'")
        with open(silence_phones_path, 'w') as f:
            f.write(f'SIL\noov\nSPN\nLAU\n')
        

        # nonsilence_phones.txt
        nonsilence_phones_path = os.path.join(dir_dict_nosp, "nonsilence_phones.txt")
        print(f"building file \'{nonsilence_phones_path}\'")
        with open(nonsilence_phones_path, 'w') as f:
            for p in sorted(phonemes):
                f.write(f'{p}\n')
        
        
        # optional_silence.txt
        optional_silence_path  = os.path.join(dir_dict_nosp, "optional_silence.txt")
        print(f"building file \'{optional_silence_path}\'")
        with open(optional_silence_path, 'w') as f:
            f.write('SIL\n')


        for corpus_name in corpora:
            save_dir = os.path.join(SAVE_DIR, corpus_name)
            if not os.path.exists(save_dir):
                os.mkdir(save_dir)
            
            # Build 'text' file
            fname = os.path.join(save_dir, 'text')
            print(f"building file \'{fname}\'")
            with open(fname, 'w') as f:
                for l in corpora[corpus_name]["text"]:
                    f.write(f"{l[0]}\t{l[1]}\n")
            
            # Build 'segments' file
            fname = os.path.join(save_dir, 'segments')
            print(f"building file \'{fname}\'")
            with open(fname, 'w') as f:
                f.writelines(corpora[corpus_name]["segments"])
            
            # Build 'utt2spk'
            fname = os.path.join(save_dir, 'utt2spk')
            print(f"building file \'{fname}\'")
            with open(fname, 'w') as f:
                f.writelines(sorted(corpora[corpus_name]["utt2spk"]))
            
            # Build 'spk2gender'
            fname = os.path.join(save_dir, 'spk2gender')
            print(f"building file \'{fname}\'")
            with open(fname, 'w') as f:
                for speaker in sorted(corpora[corpus_name]["speakers"]):
                    f.write(f"{speaker}\t{speakers_gender[speaker]}\n")
            
            # Build 'wav.scp'
            fname = os.path.join(save_dir, 'wav.scp')
            print(f"building file \'{fname}\'")
            with open(fname, 'w') as f:
                for rec_id, wav_filename in sorted(corpora[corpus_name]["wavscp"].items()):
                    f.write(f"{rec_id}\t{wav_filename}\n")
        
    
    print("\n==== STATS ====")

    for corpus in corpora:
        print(f"== {corpus.capitalize()} ==")
        audio_length_m = corpora[corpus]["audio_length"]['m']
        audio_length_f = corpora[corpus]["audio_length"]['f']
        total_audio_length = audio_length_f + audio_length_m
        print(f"- Total audio length:\t{sec2hms(total_audio_length)}")
        print(f"- Male speakers:\t{sec2hms(audio_length_m)}\t{audio_length_m/total_audio_length:.1%}")
        print(f"- Female speakers:\t{sec2hms(audio_length_f)}\t{audio_length_f/total_audio_length:.1%}")


    # print()
    # print("Pleustret gant mouezhioù :")
    # anonymous = 0
    # names = set()
    # for name in speakers:
    #     if "paotr" in name or "plach" in name or "plac'h" in name:
    #         anonymous += 1
    #     else:
    #         names.add(name.replace('_', ' ').title())
    # print(' ॰ '.join(sorted(names)))

    if args.draw_figure:
        import matplotlib.pyplot as plt
        import datetime

        plt.figure(figsize = (8, 8))

        total_audio_length = corpora["train"]["audio_length"]["f"] + corpora["train"]["audio_length"]["m"]
        keys, val = zip(*corpora["train"]["subdir_audiolen"].items())
        keys = [ k.replace('_', ' ') if v/total_audio_length>0.02 else ''
                 for k,v in corpora["train"]["subdir_audiolen"].items() ]
        
        def labelfn(pct):
            if pct > 2:
                return f"{sec2hms(total_audio_length*pct/100)}"
        plt.pie(val, labels=keys, normalize=True, autopct=labelfn)
        plt.title(f"Dasparzh ar roadennoù, {sec2hms(total_audio_length)} en holl")
        plt.savefig(os.path.join(corpora["train"]["path"], f"subset_division_{datetime.datetime.now().strftime('%Y-%m-%d')}.png"))
        print(f"\nFigure saved to \'{corpora['train']['path']}\'")
        # plt.show()
