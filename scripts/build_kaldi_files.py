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
# from math import floor, ceil

# from hashlib import md5
# from uuid import uuid4
from colorama import Fore

from ostilhou import normalize_sentence
from ostilhou.text import filter_out_chars, pre_process, split_sentences, PUNCTUATION
from ostilhou.asr import (
    phonemes,
    phonetize,
    parse_dataset
)




def sec2hms(seconds):
    """ Return a string of hours, minutes, seconds from a given number of seconds """
    minutes, seconds = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}' {seconds}''"




##############################################################################
###################################  MAIN  ###################################
##############################################################################


if __name__ == "__main__":
    desc = "Generate Kaldi training files"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--train", help="train dataset directory", required=True)
    parser.add_argument("--test", help="train dataset directory")
    parser.add_argument("--lm-corpus", nargs='+', help="path of a text file to build the language model")
    parser.add_argument("-n", "--no-lm", help="do not copy utterances to language model", action="store_true")
    # parser.add_argument("-a", "--augment", help="duplicate audio data with added noise", action="store_true")
    parser.add_argument("-d", "--dry-run", help="run script without actualy writting files to disk", action="store_true")
    parser.add_argument("-f", "--draw-figure", help="draw a pie chart showing data repartition", action="store_true")
    parser.add_argument("-v", "--verbose", help="display errors and warnings", action="store_true")
    parser.add_argument("-o", "--output", help="Output folder for generated Kalid files", default="data")
    parser.add_argument("--lm-min-token", help="Minimum number of tokens in sentence for adding it to LM corpus", type=int, default=3)
    parser.add_argument("--utt-min-len", help="Minimum length of audio utterances", type=float, default=0.0)
    args = parser.parse_args()
    print(args)

    if not os.path.isdir(args.train):
        print("`train` argument should be a directory containing aligned audio, text and split files")
        sys.exit(1)
    if args.test and not os.path.isdir(args.test):
        print("`test` argument should be a directory containing aligned audio, text and split files")
        sys.exit(1)
    
    speakers_gender = {"unknown": "u"}
    
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

        if not os.path.exists(args.output):
            os.mkdir(args.output)

        dir_kaldi_local = os.path.join(args.output, 'local')
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
                            cleaned = cleaned.replace('\xa0', ' ')
                            cleaned = filter_out_chars(cleaned, PUNCTUATION+'{}')
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
            f_out.write("!SIL SIL\n"
                        "<SPOKEN_NOISE> SPN\n"
                        "<UNK> SPN\n"
                        "<C'HOARZH> LAU\n"
                        "<NTT> SPN\n"
                        "<HUM> SPN\n"
                        "<PASAAT> SPN\n"
                        "<SONEREZH> NSN\n")
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
            f.write(f'SIL\noov\nSPN\nLAU\nMUS\n')
        

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
            save_dir = os.path.join(args.output, corpus_name)
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
        audio_length_u = corpora[corpus]["audio_length"]['u']
        total_audio_length = audio_length_f + audio_length_m + audio_length_u
        print(f"- Total audio length:\t{sec2hms(total_audio_length)}")
        print(f"- Male speakers:\t{sec2hms(audio_length_m)}\t{audio_length_m/total_audio_length:.1%}")
        print(f"- Female speakers:\t{sec2hms(audio_length_f)}\t{audio_length_f/total_audio_length:.1%}")
        if audio_length_u > 0:
            print(f"- Unknown speakers:\t{sec2hms(audio_length_u)}\t{audio_length_u/total_audio_length:.1%}")



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
        plt.savefig(os.path.join(corpora["train"]["path"], f"subset_division_{datetime.datetime.now().strftime('%Y-%m-%d')}.png"))
        print(f"\nFigure saved to \'{corpora['train']['path']}\'")
        # plt.show()
