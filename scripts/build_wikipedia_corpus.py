#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Build a text corpus from wikipedia-br dumps
Outputs text files:
    * "corpus/wiki_corpus.txt", the main corpus of sentences
    * "wikipedia_corpus/wiki_acronyms.txt", a list of possible acronyms
    * "wikipedia_corpus/wiki_capitalized.txt", a list of capitalized words
    * "wikipedia_corpus/wiki_sant.txt", a list of saints, convenient to retrieve first names
    * "wikipedia_corpus/wiki_vocab.txt", the vocabulary of the corpus

Usage: python3 build_lm_corpus.py DIR_OR_FILE -o OUTPUT_DIR

Author:  Gweltaz Duval-Guennoc
"""


import os
import re
import argparse


from ostilhou.text import (
    split_sentences,
    pre_process, filter_out_chars, sentence_stats,
    correct_sentence, normalize_sentence,
    PUNCTUATION
)
from ostilhou.hspell import get_hspell_mistakes



LIMIT_VOCAB = False
VOCAB_SIZE = 10000

KEMMADUR_PATTERN = re.compile(r" (g|b|d|w|v|c'h){1}/[a-zñ']{3,}", re.IGNORECASE)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a clean corpus text from dumps (wikiedia) or other")
    parser.add_argument("source", help="Source of raw corpus data (directory of wikipedia dumps or text files)", metavar="DIR_OR_FILE", nargs='+')
    parser.add_argument("-o", "--output", help="Output directory", default="generated")
    parser.add_argument("-t", "--min-words", help="Minimum number of words per sentence", type=int, default=3)
    parser.add_argument("-n", "--normalize", help="Normalize sentences", action="store_true")
    parser.add_argument("--rem-punct", help="Remove punctuation", action="store_true")
    args = parser.parse_args()
    print(args)

    
    # List files given as arguments, can be a directory or a single file
    filenames = []
    for d in args.source:
        if os.path.isfile(d): # and d.endswith(".txt"):
            filenames.append(d)
        elif os.path.isdir(d):
            for filename in os.listdir(d):
                # if filename.endswith(".txt"):
                filenames.append(os.path.join(d, filename))
    
    
    articles = []
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as f:
            articles.extend(f.read().split('\n\n'))
    
    keepers = []
    num_outed = 0
    vocabulary = dict()

    for article in articles:
        for line in article.split('\n'):
            #if '&' in line:
            #    line = html.unescape(line)
            
            line = filter_out_chars(pre_process(line.strip()), '"[]•')
            line = line.replace("()", '')

            for sentence in split_sentences(line):
                # Filter out short sentences
                if len(sentence) < 8:
                    continue
                
                stats = sentence_stats(sentence)
                
                if stats["words"] < args.min_words:
                    continue

                if stats["letter"]/len(sentence) < 0.4:
                    #print(f"skipped {stats['letter']/len(sentence):.2}: {sentence}")
                    continue
                
                # Filter out sentences with only single letters or short words (ex: "v i v i a n a v i v i a n a")
                if len(sentence)/stats["words"] < 2.:
                    #print(f"skipped {len(sentence)/stats['words']:.2}: {sentence}")
                    continue
                   
                # Remove all caps sentences
                if stats["upper"]/stats["letter"] > 0.8:
                    print(sentence)
                    continue
                
                sentence = correct_sentence(sentence)
                sentence = sentence.replace("J. -K.", "J.-K.")

                colored, num_errors = get_hspell_mistakes(sentence, autocorrected=True)
                if num_errors == 0:
                    keepers.append(sentence)
                elif num_errors == 1:
                    if num_outed % 200 == 0:
                        print(colored)
                    num_outed += 1

                # Collect vocabulary
                for w in filter_out_chars(sentence, PUNCTUATION).split():
                    w = w.lower()
                    if w in vocabulary:
                        vocabulary[w] += 1
                    else:
                        vocabulary[w] = 1
                
    #print(f"{num_outed} discarded sentences with 1 error")
    
    
    if LIMIT_VOCAB:
        voc_list = sorted(vocabulary.items(), key=lambda x: x[1], reverse=True)
        voc_list = voc_list[:VOCAB_SIZE]
        vocabulary.clear()
        vocabulary.update(voc_list)

    OUTPUT_DIR = args.output
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    kept = 0
    
    with open(os.path.join(OUTPUT_DIR, "wikipedia_keepers.txt"), 'w', encoding='utf-8') as f:
        #for sentence in sorted(keepers):
        for sentence in keepers:
            words = sentence.split()
            
            # Keep sentences with common words only
            for w in words:
                if LIMIT_VOCAB and not w in vocabulary:
                    break
            else:   # Executed only if previous for loop exited normally
                if args.normalize:
                    sentence = normalize_sentence(sentence)
                    if sentence_stats(sentence)["decimal"] > 0:
                        print("NORM:", sentence)
                        continue
                    
                f.write(sentence + '\n')
                kept += 1
    
    print(f"{kept} sentences kept")
    
    OUTPUT_DIR = os.path.join(OUTPUT_DIR, "extracted")
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    
    with open(os.path.join(OUTPUT_DIR, "vocab.txt"), 'w', encoding='utf-8') as f:
        for w, n in sorted(vocabulary.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{w}\t{n}\n")
