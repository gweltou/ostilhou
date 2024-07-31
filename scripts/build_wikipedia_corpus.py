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
import json
import re
import argparse
import html

from colorama import Fore

from ostilhou.text import (
    split_sentences, split_sentences_old,
    pre_process, filter_out_chars, sentence_stats,
    correct_sentence, normalize_sentence,
    PUNCTUATION
)
from ostilhou.hspell import get_hspell_mistakes



LIMIT_VOCAB = False
VOCAB_SIZE = 10000

dumps_dirs = [
    os.path.join("corpus_wikipedia", "dumps"),
    # "corpus_skrid"
]

KEMMADUR_PATTERN = re.compile(r" (g|b|d|w|v|c'h){1}/[a-zñ']{3,}", re.IGNORECASE)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a clean corpus text from dumps (wikiedia) or other")
    parser.add_argument("source", help="Source of raw corpus data (directory of wikipedia dumps or text files)", metavar="DIR_OR_FILE", nargs='+')
    parser.add_argument("-o", "--output", help="Output directory", default="generated")
    parser.add_argument("-t", "--min-tokens", help="Minimum number of valid tokens per sentence", type=int, default=4)
    parser.add_argument("-n", "--normalize", help="Normalize sentences", action="store_true")
    parser.add_argument("--rem-punct", help="Remove punctuation", action="store_true")
    args = parser.parse_args()
    print(args)

    
    # List files given as arguments
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
        with open(filename, 'r') as f:
            articles.extend(f.read().split('\n\n'))
    
    keepers = []
    raw_sentences = []
    acronym_words = set()
    capitalized_words = set()
    santou = set()
    num_outed = 0
    
    vocabulary = dict()

    for article in articles:
        for line in article.split('\n'):
            #if '&' in line:
            #    line = html.unescape(line)
            
            line = filter_out_chars(pre_process(line.strip()), '"[]•')
            line = line.replace("()", '')

            for sentence in split_sentences_old(line):
                # Filter out short sentences
                if len(sentence) < 10:
                    continue
                
                # Filter out common Wikipedia sentence patterns
                # if sentence.startswith("Diwar-benn bloavezh") or sentence.startswith("Diwar-benn ar bloavez"):
                #     continue
                # if sentence.startswith("Ar spesad a gave"):
                #     continue
                # if sentence.endswith("a annezidi o chom enni."):
                #     continue
                # if sentence.startswith("Bez' e oa") and "a annezidi e" in sentence:
                #     continue
                # if sentence.startswith("Brasaet e oa bet da"):
                #     continue
                # if sentence.startswith("Poblet eo gant"):
                #     continue
                # if sentence.startswith("Poblet e oa gant"):
                #     continue
                # if sentence.startswith("Gwelet ivez"):
                #     continue
                # if sentence.startswith("Evit implijoù all"):
                #     continue
                # if sentence.startswith("Evit sterioù all"):
                #     continue
                
                stats = sentence_stats(sentence)
                
                if stats['letter']/len(sentence) < 0.4:
                    #print(f"skipped {stats['letter']/len(sentence):.2}: {sentence}")
                    continue
                
                # Filter out sentences with only single letters or short words (ex: "v i v i a n a v i v i a n a")
                if len(sentence)/stats['words'] < 2.:
                    #print(f"skipped {len(sentence)/stats['words']:.2}: {sentence}")
                    continue
                   
                # Remove all caps sentences
                if stats["upper"]/stats["letter"] > 0.8:
                    print(sentence)
                    continue
                
                sentence = correct_sentence(sentence)
                sentence = sentence.replace("J. -K.", "J.-K.")

                if get_hspell_mistakes(sentence, autocorrected=True)[1] == 0:
                    raw_sentences.append(sentence)
                
                """
                first_word = True
                sant = False
                for w in words:
                    w = filter_out(w, punctuation)
                    if sant:
                        if w.lower() not in capitalized:
                            santou.add(w)
                        sant = False
                    elif w == "Sant" or w == "Santez":
                        sant = True
                    
                    if is_acronym(w) and w not in acronyms:
                        acronym_words.add(w)
                    elif not first_word and w.istitle() and w.isalpha() and w.lower() not in capitalized:
                        capitalized_words.add(w)
                    first_word = False
                """
                
                sub_sentences = sentence.split(', ')
                sub_keepers = []
                for sub in sub_sentences:
                    if not sub.strip(): continue

                    correction, num_errors = get_hspell_mistakes(sub, autocorrected=True)

                    if num_errors == 0 and len(correction) > 1:
                        sub_keepers.append(sub)
                    elif num_errors == 1:
                        if num_outed % 200 == 0:
                           print(correction)
                        num_outed += 1
                sentence = ', '.join(sub_keepers)
                # keepers.add(sentence)
                keepers.append(sentence)
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

    with open(os.path.join(OUTPUT_DIR, "raw_sentences.txt"), 'w') as f:
        for sentence in raw_sentences:
            f.write(sentence + '\n')
    
    kept = 0
    
    with open(os.path.join(OUTPUT_DIR, "corpus.txt"), 'w') as f:
        #for sentence in sorted(keepers):
        for sentence in keepers:
            words = sentence.split()
            
            # Filter out short sentences
            if len(words) < args.min_tokens:
                continue

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
    
    """
    with open(os.path.join(OUTPUT_DIR, "acronyms.txt"), 'w') as f:
        for a in sorted(acronym_words):
            f.write(a + '\n')
    with open(os.path.join(OUTPUT_DIR, "capitalized.txt"), 'w') as f:
        for w in sorted(capitalized_words):
            f.write(w + '\n')
    with open(os.path.join(OUTPUT_DIR, "sant.txt"), 'w') as f:
        for w in sorted(santou):
            f.write(w + '\n')
    """
    with open(os.path.join(OUTPUT_DIR, "vocab.txt"), 'w') as f:
        for w, n in sorted(vocabulary.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{w}\t{n}\n")
