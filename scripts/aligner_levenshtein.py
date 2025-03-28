from typing import List
import sys

import jiwer
from pathlib import Path
import json

from ostilhou.asr.aligner import prepare_text_for_alignment
from ostilhou.asr.recognizer import transcribe_file_timecoded



def prep_word(word: str) -> str:
    # word = word.lower().replace("c'h", 'X')
    # return strip_punct(word)
    return prepare_text_for_alignment(word)


def align_texts_with_vosk_tokens(text: str, vosk_tokens: List[dict]) -> dict:
    # Flatten text
    text = text.replace('\n', ' ').replace('-', ' ')

    # Create matrix
    gt_words = [prep_word(w) for w in text.split()]
    gt_words = list(filter(lambda x: x, gt_words))

    hyp_words = [prep_word(t["word"]) for t in vosk_tokens]

    n, m = len(gt_words), len(hyp_words)
    dp = [[float('inf')] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0

    del_cost = 1.0
    ins_cost = 1.0
    
    # Fill the matrix using Levenshtein distance
    for i in range(n + 1):
        for j in range(m + 1):
            if i > 0 and j > 0:
                if gt_words[i-1] == hyp_words[j-1]:
                    cost = 0 
                else:
                    cost = jiwer.cer(gt_words[i-1], hyp_words[j-1])
                dp[i][j] = min(dp[i][j], dp[i-1][j-1] + cost)
            if i > 0:
                dp[i][j] = min(dp[i][j], dp[i-1][j] + del_cost)  # deletion
            if j > 0:
                dp[i][j] = min(dp[i][j], dp[i][j-1] + ins_cost)  # insertion
    # print_matrix(dp)
    
    # Backtrack to find alignment
    alignment = []
    i, j = n, m
    while i > 0 or j > 0:
        sub_cost = jiwer.cer(gt_words[i-1], hyp_words[j-1])
        if (i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + sub_cost):
            alignment.append((gt_words[i-1], hyp_words[j-1]))
            i, j = i-1, j-1
        elif i > 0 and dp[i][j] == dp[i-1][j] + del_cost:
            alignment.append((gt_words[i-1], None))
            i -= 1
        else:
            alignment.append((None, hyp_words[j-1]))
            j -= 1
    
    return {'alignment': list(reversed(alignment))}


def print_matrix(matrix):
    # 2D matrix
    for row in matrix:
        r = [ f"{val:.2f}" for val in row ]
        print(f"[{' '.join(r)}]")



if __name__ == "__main__":
    with open(sys.argv[2], 'r') as _f:
        text = _f.read()

    cached_transcription = Path(sys.argv[1]).with_suffix(".json")
    if cached_transcription.exists():
        with open(cached_transcription, 'r') as _f:
            hyp = json.load(_f)
    else:
        hyp = transcribe_file_timecoded(sys.argv[1])


    result = align_texts_with_vosk_tokens(text, hyp)

    # print(f"WER: {result['wer']:.2%}")
    # print(f"MER: {result['mer']:.2%}")
    # print(f"WIL: {result['wil']:.2%}")
    print("\nAlignment:")
    alignment = result['alignment']
    gt_i, hyp_i = 0, 0
    for gt, h in alignment:
        timecodes = f"{round(hyp[hyp_i]['start'], 1)} - {round(hyp[hyp_i]['end'], 1)}" if h else ''
        print(f"{gt if gt else '_':<12} | {hyp[hyp_i]['word'] if h else '_':<12} | {timecodes}")
        if gt:
            gt_i += 1
        if h:
            hyp_i += 1