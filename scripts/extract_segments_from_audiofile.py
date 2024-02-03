#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    File: extract_segments_from_audiofiles.py

    Creates many single utterance audio files from a long audiofile.

    Usage:
        python3 extract_segments_from_audiofiles.py long_audio.mp3 -o utterances
    
    Author: Gweltaz Duval-Guennoc (2023)
"""

import os
import argparse

from ostilhou.asr import transcribe_file_timecoded, load_vosk
from ostilhou.audio import split_to_segments, load_audiofile, get_audio_segment


def save_segments(segments, filename):
	with open(filename, 'w') as f:
		for _, s in enumerate(segments):
			start = int(s[0])
			stop =  int(s[1])
			f.write(f"{start} {stop}\n")
	print('split file saved')


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('audiofile')
	parser.add_argument('-o', '--output', type=str, default="extracted_words",
						help="Output folder")
	parser.add_argument('--min-sil-length', type=int, help="Minimum silence length (millisecs)", default=500)
	parser.add_argument('--padding', type=int, default=200,
						help="Add padding left and right of segment (millisecs)")
	parser.add_argument("-m", "--model", help="Vosk model to use for decoding", metavar='MODEL_PATH')
	args = parser.parse_args()
	
	if args.model:
		load_vosk(args.model)

	words = transcribe_file_timecoded(args.audiofile)
	segments = []
	current_seg = []
	for w in words:
		if not current_seg:
			current_seg = [ w["word"], w["start"], w["end"] ]
		elif w["start"] - current_seg[2] < args.min_sil_length/1000:
			# Concat with previous segment
			current_seg = [
				' '.join([current_seg[0], w["word"]]),
				current_seg[1],
				w["end"]
				]
		else:
			# New segment
			segments.append(current_seg)
			current_seg = [ w["word"], w["start"], w["end"] ]
	segments.append(current_seg)

	song = load_audiofile(args.audiofile)
	print("Framerate:", song.frame_rate)
	print("Sample width:", song.sample_width)
	print("Num channels:", song.channels)
	
	if not os.path.exists(args.output):
		os.mkdir(args.output)

	for segment in segments:
		print(segment[0])
		seg_name = segment[0].replace(' ', '_')
		seg = song[int(segment[1]*1000)-args.padding:int(segment[2]*1000)+args.padding]
		seg_path = os.path.join(args.output, seg_name) + ".wav"
		seg.export(seg_path, format="wav")
	
	print("Number of segments extracted:", len(segments))
