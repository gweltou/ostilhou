#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
	Converts a folder of audio and subtitle files downloaded with youtube-dl,
	to local dataset format

	Usage:
		python3 convert_youtube-dl.py SOURCE_DIR [-o OUTPUT_DIR]

	youtube-dl command:
		youtube-dl --download-archive ${DOWNLOAD_DIR}/downloaded.txt --rm-cache-dir -cwi --no-post-overwrites -o ${DOWNLOAD_DIR}'/%(playlist_index)s-%(title)s.%(ext)s' --cookies=cookies.txt --write-sub --sub-lang br --sub-format vtt --extract-audio --audio-format mp3 https://www.youtube.com/playlist?list=$PLAYLIST
"""


import os
import glob
from shutil import copyfile

import argparse

from ostilhou.audio import convert_to_wav, convert_to_mp3
from ostilhou.asr import load_segments_data, load_text_data
from ostilhou.text import (
    normalize_sentence, pre_process, filter_out_chars,
	is_full_sentence, is_sentence_start_open, is_sentence_end_open,
	PUNCTUATION
)
from ostilhou.hspell import get_hspell_mistakes

from srt2seg import srt2segments


# Short list of audio documents that have been manually verified
skipfile_path = "/home/gweltaz/STT/corpora/brezhoweb/skip.tsv"


def stage0():
	print("Stage 0 : file conversion")
	
	if args.output:
		if not os.path.exists(args.output):
			os.mkdir(args.output)
			print("Created folder", args.output)
	
	file_list = glob.glob(args.folder + "/*.vtt")
	
	with open(skipfile_path, 'r') as f:
		skipfiles = [l.strip() for l in f.readlines()]
	
	audio_ext = os.path.extsep + args.audio_format

	for file in file_list:
		print(file)
		new_file = file.replace(".br.vtt", ".vtt")
		basename = os.path.split(os.path.splitext(new_file)[0])[1]
		if basename in skipfiles:
			print("**** skipping ****")
			continue

		# Renaming files
		source_audio_file = new_file.replace(".vtt", ".mp3")
		new_file = new_file.replace('&', '_')
		new_file = new_file.replace(' ', '_')
		new_file = new_file.replace("'", '')
		new_file = new_file.replace("(", '')
		new_file = new_file.replace(")", '')
		new_file = new_file.replace(",", '')

		if args.output:
			new_file = os.path.join(args.output, os.path.split(new_file)[1])
		copyfile(file, new_file)
		
		if not os.path.exists(source_audio_file):
			print("Couldn't find", source_audio_file)
			continue
		
		# Audio conversion
		audio_file = new_file.replace(".vtt", audio_ext)
		if args.output:
			audio_file = os.path.join(args.output, os.path.split(audio_file)[1])
		if not os.path.exists(audio_file):
			if args.audio_format == 'mp3':
				convert_to_mp3(source_audio_file, audio_file, keep_orig=not args.remove)
			else:
				convert_to_wav(source_audio_file, audio_file, keep_orig=not args.remove)
		
		# segments and text extraction
		srt2segments(new_file)

		# Remove original vtt subtitle file if necessary
		if args.output and args.output != args.folder:
			os.remove(new_file)


def stage1():
	"""Convert text to lowercase for baseline model"""

	print("Stage 1: lowercase")

	file_list = glob.glob(args.folder + "/*.seg")

	for segment_file in file_list:
		text_file = segment_file.replace(".seg", ".txt")
		text = [ t[0] for t in load_text_data(text_file) ]

		text = [ pre_process(s).lower() for s in text ]
		
		if args.dry_run:
			continue

		with open(text_file, 'w') as fout:
			fout.writelines([t+'\n' for t in text])


def stage2():
	"""Normalize text segments"""
	
	print("Stage 2 : normalization and cherry-picked correction")
	
	# Use a specific word substitution file
	sub_file = "/home/gweltaz/STT/corpora/brezhoweb/substitution.tsv"
	sub_dict = dict()
	with open(sub_file, 'r') as fin:
		for line in fin.readlines():
			line = line.split('\t')
			sub_dict[line[0]] = line[1].strip()
	
	file_list = glob.glob(args.folder + "/*.seg")
	total_mistakes = 0
	total_kept_sentences = 0

	for segment_file in file_list:
		segments = load_segments_data(segment_file)
		text_file = segment_file.replace(".seg", ".txt")
		text = [ t[0] for t in load_text_data(text_file) ]
		
		kept_text = []
		kept_segs = []
		
		for seg, sentence in zip(segments, text):
			sentence = pre_process(sentence)
			for word in sub_dict:
				if word in sentence:
					sentence = sentence.replace(word, sub_dict[word])
			norm_sentence = normalize_sentence(sentence, autocorrect=True, norm_punct=True)
			norm_sentence = norm_sentence.replace('-', ' ')
			corr, n_mistake = get_hspell_mistakes(norm_sentence, autocorrected=True)
			n_words = len(filter_out_chars(norm_sentence, PUNCTUATION).split())
			if n_mistake <= n_words // 7: # Only sentences with less than 15% errors are kept
				kept_text.append(norm_sentence)
				kept_segs.append(seg)
				total_kept_sentences += 1
				if n_mistake > 1:
					total_mistakes += n_mistake
			else:
				print(corr)
		
		if args.dry_run:
			continue
		
		with open(text_file, 'w') as fout:
			fout.writelines([t+'\n' for t in kept_text])

		with open(segment_file, 'w') as fout:
			fout.writelines([f"{s[0]} {s[1]}\n" for s in kept_segs])
		
	print("Num mistakes:", total_mistakes)
	print("Kept sentences:", total_kept_sentences)


def stage3():
	"""Joining segments from the same sentence (when possible)"""
	
	print("Stage 3 : joining segments")

	file_list = glob.glob(args.folder + "/*.seg")
	total_segments_before = 0
	total_segments_after = 0

	for segment_file in file_list:
		segments = load_segments_data(segment_file)
		text_file = segment_file.replace(".seg", ".txt")
		text = [ t[0] for t in load_text_data(text_file) ]
		
		total_segments_before += len(segments)
		joined_text = []
		joined_segs = []
		
		for i, t in enumerate(text):
			t = ' '.join(t.strip().split()) # Remove multi spaces

			# First line in file
			if not joined_text:
				joined_text.append(t)
				joined_segs.append(segments[i])
				continue

			if is_sentence_start_open(t) and is_sentence_end_open(joined_text[-1]):
				# Measure time gap between this line and previous line
				sil = segments[i][0] - joined_segs[-1][1]
				# Expected length after joining the two segments together
				joined_len = segments[i][1] - joined_segs[-1][0]
				if sil < 1500 and joined_len < 9000:
					# Join this segment with previous one
					joined_text[-1] += ' ' + t
					joined_segs[-1] = (joined_segs[-1][0], segments[i][1])
					continue
			
			if is_full_sentence(t) and is_full_sentence(joined_text[-1]):
				# Measure time gap between this line and previous line
				sil = segments[i][0] - joined_segs[-1][1]
				# Expected length after joining the two segments together
				joined_len = segments[i][1] - joined_segs[-1][0]
				if sil < 2000 and joined_len < 6000:
					# Join this segment with previous one
					joined_text[-1] += ' ' + t
					joined_segs[-1] = (joined_segs[-1][0], segments[i][1])
					continue

			joined_text.append(t)
			joined_segs.append(segments[i])
		

		total_segments_after += len(joined_segs)
		if args.dry_run:
			continue
		
		with open(text_file, 'w') as fout:
			#fout.write("{source: }\n{source-audio: }\n{author: }\n{licence: }\n{tags: }\n\n\n\n\n\n")
			fout.writelines([t+'\n' for t in joined_text])

		with open(segment_file, 'w') as fout:
			fout.writelines([f"{s[0]} {s[1]}\n" for s in joined_segs])
		
	print("Segments before:", total_segments_before)
	print("Segments after:", total_segments_after)



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('folder')
	parser.add_argument('-o', '--output', type=str, help="Destination folder")
	parser.add_argument('--remove', action='store_true', help="Remove original files (audio and subs)")
	parser.add_argument('--stage', type=int, default=1)
	parser.add_argument("--audio-format", help="Audio format of exported segments", choices=['wav', 'mp3'], default='mp3')
	parser.add_argument('-d', '--dry-run', action='store_true', help="Do not write to disk")
	args = parser.parse_args()

	# File conversion
	stage0()
	
	if args.output and args.output != args.folder:
		args.folder = args.output

	if args.stage == 1:
		# Prepare data for baseline model
		stage1()
	if args.stage >= 2:
		# Normalization
		stage2()
	if args.stage >= 3:
		# Segment concatenation
		stage3()
