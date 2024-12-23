#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
import sys

import jiwer
import re
from math import inf

from tqdm import tqdm

from ..text import pre_process, filter_out_chars, PUNCTUATION



def _count_words(s: str) -> int:
    s = re.sub(r"{.+?}", '', s)
    s = filter_out_chars(pre_process(s), PUNCTUATION + "'")
    s = s.replace('-', ' ')
    return len(s.split())


def _prepare_text(s: str) -> str:
    """ Process sentence for alignment matching """
    s = re.sub(r"{.+?}", '', s) # Ignore metadata
    s = re.sub(r"<[A-Z\']+?>", '', s) # Ignore special tokens
    s = pre_process(s.lower())
    s = s.replace("c'h", 'X').replace('ch', 'S')
    s = s.replace('ù', 'u').replace('ê', 'e')
    s = filter_out_chars(s, PUNCTUATION + " '-h ")
    # Remove double-letters
    chars = []
    for c in s:
        if not chars:
            chars.append(c)
        elif c != chars[-1]:
            chars.append(c)
    s = ''.join(chars)
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
    norm_sentences = [ _prepare_text(s) for s in sentences ]

    # Remove empty lines
    norm_sentences = [s for s in norm_sentences if s]
    
    total_ref_words = sum(n_ref_words)
    total_hyp_words = len(hyp)
    matches = []

    if progress_bar:
        norm_sentences = tqdm(norm_sentences)
    
    for sent_idx, norm_sentence in enumerate(norm_sentences):
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
                hyp_sentence = _prepare_text(hyp_sentence)
                score = (
                    jiwer.cer(norm_sentence, hyp_sentence) * (1.0 - positional_weight) +
                    dist * positional_weight
                )
                if score <= best_score:
                    best_hyp = hyp_windowed
                    best_span = (i, i+offset)
                    best_score = score
                    # print(score, hyp_sentence)
                else:
                    break
            
            match.append( {"hyp": best_hyp, "span": best_span, "score": best_score} )

        match.sort(key=lambda x: x["score"])
        
        # Keep only best match location for each sentence
        try:
            match[0]["sentence"] = sentences[sent_idx]
            assert match[0]["span"][0] < match[0]["span"][1], f"wrong segment {match[0]}"
            matches.append(match[0])
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



def add_reliability_score(matches: list, hyp: list, verbose=False):
    """
        Infer the reliability of each location by checking its adjacent neighbours
        Modifies `matches` in-place
    """
    
    last_reliable_wi = 0
    for i, match in enumerate(matches):
        if not match: # Empty or metadata only lines
            continue

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

        matches[i]["reliability"] = r
        
        if verbose:
            print(f"{i} {span}\t{r}", file=sys.stderr)



def get_unaligned_ranges(sentences, matches, rel=['O']):
    """ Find ill-aligned sentence ranges """
    
    wrong_ranges = []
    start = 0
    end = 0
    while True:
        while start < len(sentences) and matches[start]["reliability"] in rel:
            start += 1
        end = start
        while end < len(sentences) and matches[end]["reliability"] not in rel:
            end += 1
        if start >= len(sentences):
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
    """ Returns the word index """
    sentence_a = _prepare_text(sentence_a)
    sentence_b = _prepare_text(sentence_b)
    best_score = 999
    best_cut = -1
    for i in range(1, len(hyp)):
        hyp_a = _prepare_text(''.join([ t["word"] for t in hyp[:i] ]))
        hyp_b = _prepare_text(''.join([ t["word"] for t in hyp[i:] ]))
        score = jiwer.cer(sentence_a, hyp_a) + jiwer.cer(sentence_b, hyp_b)
        if score < best_score:
            best_score = score
            best_cut = i
    # hyp = [ t["word"] for t in hyp ]
    return best_cut



def resolve_boundaries(matches: list, max_dist=2):
    """
        Resolve boundary conflicts between overlapping matches
        Modifies `matches` in-place
    """

    for m in range(len(matches) - 1):
        prev, next = matches[m:m+2]
        overlap = prev["span"][1] - next["span"][0]
        if 0 < overlap <= max_dist:
            # End of prev goes beyond start of next
            hyp = prev["hyp"][:-overlap] + next["hyp"]
            i = find_best_cut(prev["sentence"], next["sentence"], hyp)
            diff = len(prev["hyp"]) - i
            pstart, pend = prev["span"]
            pend -= diff
            prev["span"] = (pstart, pend)
            prev["hyp"] = hyp[:i]
            _, nend = next["span"]
            next["span"] = (pend, nend)
            next["hyp"] = hyp[i:]



def calculate_global_score(matches: list):
    total_score = 0
    total_num_char = 0
    for match in matches:
        if not match:
            continue
        num_char = len(_prepare_text(match["sentence"]))
        total_score += match["score"] * num_char
        total_num_char += num_char

    return total_score / total_num_char