#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Score the alignment of an ali file, given a reference ali file
    
    Usage: ./compare_alignment.py ref.ali hyp.ali
"""

import sys

from ostilhou.asr import load_ali_file


if __name__ == "__main__":
    ref = load_ali_file(sys.argv[1])
    hyp = load_ali_file(sys.argv[2])

    assert len(ref["segments"]) == len(hyp["segments"]), f"{len(ref["segments"])=}, {len(hyp["segments"])=}"

    score = 0

    for ref_seg, hyp_seg in zip(ref["segments"], hyp["segments"]):
        d_start = ref_seg[0] - hyp_seg[0]
        d_start *= d_start
        d_end = ref_seg[1] - hyp_seg[1]
        d_end *= d_end
        print(ref_seg, hyp_seg, round(d_start + d_end, 2))
        score += d_start + d_end
    
    print(f"Alignment score: {score/len(ref["segments"])}")