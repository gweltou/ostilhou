#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
from pathlib import Path

import pandas as pd

from evaluatio.metrics.wer import (
    word_error_rate,
    word_error_rate_ci,
    word_error_rate_per_pair,
)
from evaluatio.inference.hypothesis import paired_bootstrap_test


column_names = [
    "filepath", 
    "audio_ext", 
    "start", 
    "end", 
    "sentence", 
    "transcription"
]


def main(
        transcription_file1: str,
        transcription_file2: str|None
        ):

    df = pd.read_csv(
        Path(transcription_file1), 
        sep="\t", 
        header=None, 
        names=column_names
    )

    if transcription_file2:
        df2 = pd.read_csv(
            Path(transcription_file2), 
            sep="\t", 
            header=None, 
            names=column_names
        )
        df = pd.merge(
            df, 
            df2[["filepath", "start", "end", "transcription"]], 
            on=["filepath", "start", "end"], 
            suffixes=("_a", "_b")
        )


    # 'sentence' = Ground Truth (Reference)
    # 'transcription' = Model Output (Prediction)
    ref_col = "sentence"

    # --- MODEL COMPARISON ---
    # Note: To compare models, your TSV needs a second transcription column 
    # (e.g., 'transcription_model_b'). 
    # If you only have one model, you can skip the code below.

    if "transcription_b" in df.columns:
        df["transcription_b"] = df["transcription_b"].astype(str)

        wer_a = word_error_rate_per_pair(df[ref_col], df["transcription_a"])
        wer_b = word_error_rate_per_pair(df[ref_col], df["transcription_b"])
        model_a_ci = word_error_rate_ci(df[ref_col], df["transcription_a"], 5000, 0.95)
        model_b_ci = word_error_rate_ci(df[ref_col], df["transcription_b"], 5000, 0.95)

        pvalue = paired_bootstrap_test(wer_a, wer_b, iterations=5000)

        def ci_plus_minus(ci):
            delta = ci.upper - ci.mean
            return f"{ci.mean:.3f} ± {delta:.3f}"

        print(f"Model 1 WER: {ci_plus_minus(model_a_ci)}")
        print(f"Model 2 WER: {ci_plus_minus(model_b_ci)}")
        print(f"P-value: {pvalue}")
    else:
        pred_col = "transcription"
        df[ref_col] = df[ref_col].astype(str)
        df[pred_col] = df[pred_col].astype(str)

        # Corpus-level WER
        wer = word_error_rate(df[ref_col], df[pred_col])

        # Confidence interval
        ci = word_error_rate_ci(df[ref_col], df[pred_col], 5000, 0.95)

        print(f"WER: {ci.mean:.3f} ± {ci.upper - ci.mean:.3f}")


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(
    #     description="Calculate WER and CER from a decode file"
    # )
    # parser.add_argument("data_folder", metavar='FOLDER',
    #     help="Folder containing ALI files or a single ALI file or a text file with a list of paths in it")
    # parser.add_argument("-o", "--output", type=str, help="Results file")
    # parser.add_argument("--noise", type=float, help="Add white noise to audio (dB)")
    # parser.add_argument("-v", "--verbose", action="store_true")
    # args = parser.parse_args()

    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.argv[1], None)