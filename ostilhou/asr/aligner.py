#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
import sys

import jiwer
import re
from math import inf

from tqdm import tqdm

from ..text import (
    pre_process, filter_out_chars,
    sentence_stats, normalize_sentence,
    PUNCTUATION,
)



def _count_words(s: str) -> int:
    s = re.sub(r"{.+?}", '', s)
    s = filter_out_chars(pre_process(s), PUNCTUATION + "'")
    s = s.replace('-', ' ')
    return len(s.split())


def prepare_text_for_alignment(s: str) -> str:
    """ Process sentence for alignment matching """
    s = re.sub(r"{.+?}", '', s) # Ignore metadata
    s = re.sub(r"<[A-Z\']+?>", '', s) # Ignore special tokens
    s = pre_process(s.lower())
    if sentence_stats(s)["decimal"] > 0:
        s = normalize_sentence(s, autocorrect=True)
    s = s.replace("c'h", 'X').replace('ch', 'S')
    s = s.replace('ù', 'u').replace('ê', 'e')
    # Remove double-letters
    chars = []
    for c in s:
        if not chars:
            chars.append(c)
        elif c != chars[-1]:
            chars.append(c)
    s = ''.join(chars)
    s = filter_out_chars(s, PUNCTUATION + " '-h ")
    return s



def align(
        sentences:list,
        hyp:List[dict],
        left_boundary:int, right_boundary:int,
        positional_weight=0.5,
        progress_bar=True
    ):
    """
        Try to locate the best match for each sentence in transcription
        Returns a list of match dictionaries.
        
        Args:
            sentences (list of str): List of reference sentences
            hyp (list of vosk tokens (dicts)): List of timecoded words for
                the whole text.
            left_boudary (int): restrict search from this word index
            right_boundary (int): restrict search up to this word index
            positional_weight (float): weight (from 0.0 to 1.0) to apply to
                the relative position of the sentence in the transcript when
                trying to find its alignment. A weight > 0.0 can help when
                there's many occurences of the same sentence in the transcript.
        
        Returns:
            list: List of matches dictionaries of the form:
                {'sentence', 'hyp', 'span', 'score'}
                Where:
                    sentence (str): original reference sentence
                    hyp (list): list of timecoded inference tokens
                    span (tuple): start and end token indexes in global hypothesis
                    score (float): CER score for this alignment
    """
    
    n_ref_words = [ _count_words(s) for s in sentences ]
    # norm_sentences = [ _prepare_text(s) for s in sentences ]

    # Remove empty lines
    # norm_sentences = [s for s in norm_sentences if s]
    
    total_ref_words = sum(n_ref_words)
    total_hyp_words = len(hyp)
    matches = []

    if progress_bar:
        sentences = tqdm(sentences)
    
    for sent_idx, sentence in enumerate(sentences):
        norm_sentence = prepare_text_for_alignment(sentence)
        if not norm_sentence:
            continue

        match = []
        sentence_pos = left_boundary + sum(n_ref_words[:sent_idx]) / total_ref_words
        for i in range(left_boundary, right_boundary):
            # Try to find a minima for the CER by adding one word at a time
            hyp_pos = i / total_hyp_words
            dist = abs(hyp_pos - sentence_pos)
            # dist *= dist
            best_score = inf
            for offset in range(1, right_boundary - i + 1):
                hyp_windowed = hyp[i: i+offset]
                hyp_sentence = ''.join( [t["word"] for t in hyp_windowed] )
                hyp_sentence = prepare_text_for_alignment(hyp_sentence)
                score = (
                    jiwer.cer(norm_sentence, hyp_sentence) * (1.0 - positional_weight) +
                    dist * positional_weight
                )
                if score <= best_score:
                    best_hyp = hyp_windowed
                    best_span = (i, i+offset)
                    best_score = score
                else:
                    break
            
            match.append( {"hyp": best_hyp, "span": best_span, "score": best_score} )

        match.sort(key=lambda x: x["score"])
        
        # Keep only best match location for each sentence
        try:
            best_match = match[0]
            best_match["sentence"] = sentence.strip()
            assert best_match["span"][0] < best_match["span"][1], f"wrong segment {best_match}"
            matches.append(best_match)
        except:
            print(f"{match=}")
            print(f"{norm_sentence=}")
            print(f"{left_boundary=} {right_boundary=}")
            return []

    return matches



def get_prev_word_idx(matches, idx):
    if idx <= 0:
        return 0
    return matches[idx-1]["span"][1]

def get_next_word_idx(matches, idx, hyp):
    if idx >= len(matches) - 1:
        return len(hyp)
    return matches[idx+1]["span"][0]



def add_reliability_score(matches:list, hyp:list, verbose=False):
    """
    Infer the reliability of each location by checking its adjacent neighbours
    Modifies `matches` in-place
    """
    
    last_reliable_wi = 0
    for i, match in enumerate(matches):
        # if not match: # Empty or metadata only lines
        #     continue

        span = match["span"]
        prev_dist = get_prev_word_idx(matches, i) - span[0]
        next_dist = get_next_word_idx(matches, i, hyp) - span[1]
        # Allow for up to 2 words overlap between neighbours
        is_pdn = abs(prev_dist) <= 2 # is prev a direct-ish neighbour ?
        is_ndn = abs(next_dist) <= 2 # is next a direct-ish neighbour ?
        # is_pdn = prev_dist == 0
        # is_ndn = next_dist == 0
        if is_pdn or is_ndn and (span[1] > last_reliable_wi):
            r = 'o' # Semi-reliable alignment
            if is_pdn and is_ndn and (abs(prev_dist) + abs(next_dist)) <= 2:
                r = 'O' # Reliable alignment
                last_reliable_wi = span[1]
        elif span[1] > last_reliable_wi:
            r = '?' # Not sure...
        else:
            r = 'X' # Obviously wrong alignment

        match["reliability"] = r
        
        if verbose:
            print(f"{i} {span}\t{r}", file=sys.stderr)



def get_unaligned_ranges(matches, rel=['O']) -> List:
    """Find ill-aligned sentence ranges"""
    
    wrong_ranges = []
    start = 0
    end = 0
    while True:
        while start < len(matches) and matches[start]["reliability"] in rel:
            start += 1
        end = start
        while end < len(matches) and matches[end]["reliability"] not in rel:
            end += 1
        if start >= len(matches):
            break
        wrong_ranges.append((start, end))
        start = end
    return wrong_ranges



def count_aligned_utterances(matches: list):
    n = 0
    for match in matches:
        if not match:
            continue
        if match["reliability"] == 'O':
            n += 1
    return n



def find_best_cut(sentence_a, sentence_b, hyp) -> int:
    """Return the word index of best cut in given hypothesis tokens"""
    sentence_a = prepare_text_for_alignment(sentence_a)
    sentence_b = prepare_text_for_alignment(sentence_b)
    best_score = inf
    best_cut = -1
    for i in range(1, len(hyp)):
        hyp_a = prepare_text_for_alignment(''.join([ t["word"] for t in hyp[:i] ]))
        hyp_b = prepare_text_for_alignment(''.join([ t["word"] for t in hyp[i:] ]))
        score = jiwer.cer(sentence_a, hyp_a) + jiwer.cer(sentence_b, hyp_b)
        if score < best_score:
            best_score = score
            best_cut = i
    return best_cut



def resolve_boundaries(matches: list, max_dist=2):
    """
        Resolve boundary conflicts between overlapping matches
        Modifies `matches` in-place
    """

    for m in range(len(matches) - 1):
        prev, next = matches[m:m+2]
        if next["span"][0] < prev["span"][0]:
            continue
        overlap = prev["span"][1] - next["span"][0]
        if 0 < overlap <= max_dist:
            # End of prev goes past start of next
            combined_hyp = prev["hyp"][:-overlap] + next["hyp"]
            i = find_best_cut(prev["sentence"], next["sentence"], combined_hyp)
            diff = len(prev["hyp"]) - i
            if diff >= len(prev["hyp"]):
                continue
            p_start, p_end = prev["span"]
            p_end -= diff
            prev["span"] = (p_start, p_end)
            prev["hyp"] = combined_hyp[:i]
            _, n_end = next["span"]
            next["span"] = (p_end, n_end)
            next["hyp"] = combined_hyp[i:]



def calculate_global_score(matches: list):
    total_score = 0
    total_num_char = 0
    for match in matches:
        if not match:
            continue
        num_char = len(prepare_text_for_alignment(match["sentence"]))
        total_score += match["score"] * num_char
        total_num_char += num_char

    return total_score / total_num_char