#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
	Converts a folder of audio and subtitle files downloaded with youtube-dl,
	to local dataset format

	Usage:
		python3 convert_youtube-dl.py DOWNLAD_DIR [-o OUTPUT_DIR]

	youtube-dl command:
		youtube-dl --download-archive ${DOWNLOAD_DIR}/downloaded.txt --rm-cache-dir -cwi --no-post-overwrites -o ${DOWNLOAD_DIR}'/%(playlist_index)s-%(title)s.%(ext)s' --cookies=cookies.txt --write-sub --sub-lang br --sub-format vtt --extract-audio --audio-format mp3 https://www.youtube.com/playlist?list=$PLAYLIST
"""


import os
import glob
from shutil import copyfile
import re

import argparse

from ostilhou.audio import convert_to_wav
from ostilhou.asr import load_segments_data, load_text_data
from ostilhou.text import normalize_sentence, pre_process, filter_out_chars, PUNCTUATION
from ostilhou.hspell import get_hspell_mistakes

from srt2seg import srt2segments



def stage1():
	"""
	"""
	
	print("Stage 1")
	
	if args.output:
		if not os.path.exists(args.output):
			os.mkdir(args.output)
			print("Created folder", args.output)

	file_list = glob.glob(args.folder + "/*.vtt")
	
	for file in file_list:
		print(file)
		new_file = file.replace(".br.vtt", ".vtt")
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
		# else:
		# 	os.rename(file, new_file)
		
		if not os.path.exists(source_audio_file):
			print("Couldn't find", source_audio_file)
			continue
		
		wav_file = new_file.replace(".vtt", ".wav")
		if args.output:
			wav_file = os.path.join(args.output, os.path.split(wav_file)[1])

		if not os.path.exists(wav_file):
			convert_to_wav(source_audio_file, wav_file, keep_orig=not args.remove)
		
		srt2segments(new_file)

		# Remove subtitle file if necessary
		if args.output and args.output != args.folder:
			os.remove(new_file)
		


def stage2():
	"""
		Normalize text segments
	"""
	
	print("Stage 2")
	
	# Use a specific word substitution file
	sub_file = "/home/gweltaz/STT/corpora/brezhoweb/substitution.tsv"
	sub_dict = dict()
	with open(sub_file, 'r') as fin:
		for line in fin.readlines():
			line = line.split('\t')
			sub_dict[line[0]] = line[1].strip()
	
	if args.output:
		file_list = glob.glob(args.output + "/*.seg")
	else:
		file_list = glob.glob(args.folder + "/*.seg")
	
	total_mistakes = 0
	total_kept_sentences = 0
	for file in file_list:
		#print("======", file, "======")
		wav_file = file.replace(".seg", ".wav")
		text_file = wav_file.replace(".wav", ".txt")
		segment_file = wav_file.replace(".wav", ".seg")
		text = [ t[0] for t in load_text_data(text_file) ]
		segments = load_segments_data(segment_file)
		
		kept_text = []
		kept_segs = []
		
		for seg, sentence in zip(segments, text):
			sentence = pre_process(sentence)
			for word in sub_dict:
				if word in sentence:
					sentence = sentence.replace(word, sub_dict[word])
			# sentence = re.sub(r"^-(?=[A-Z])", "– ", sentence)
			norm_sentence = normalize_sentence(sentence, autocorrect=True)
			norm_sentence = norm_sentence.replace('-', ' ')
			corr, n_mistake = get_hspell_mistakes(norm_sentence)
			n_words = len(filter_out_chars(norm_sentence, PUNCTUATION).split())
			if n_mistake <= n_words // 6:
				kept_text.append(norm_sentence)
				kept_segs.append(seg)
				total_kept_sentences += 1
				if n_mistake > 1:
					total_mistakes += n_mistake
					#print(corr)
			else:
				print(corr)
		#print()
		if args.dry_run:
			continue
		
		with open(text_file, 'w') as fout:
			#fout.write("{source: }\n{source-audio: }\n{author: }\n{licence: }\n{tags: }\n\n\n\n\n\n")
			fout.writelines([t+'\n' for t in kept_text])

		with open(segment_file, 'w') as fout:
			fout.writelines([f"{s[0]} {s[1]}\n" for s in kept_segs])
		
	print("Num mistakes:", total_mistakes)
	print("Kept sentences:", total_kept_sentences)
	




if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('folder')
	parser.add_argument('-o', '--output', type=str, help="Destination folder")
	parser.add_argument('--remove', action='store_true', help="Remove original files (audio and subs)")
	parser.add_argument('--stage', type=int, default=1)
	parser.add_argument('-d', '--dry-run', action='store_true', help="Do not write to disk")
	args = parser.parse_args()

	if args.stage == 1:
		stage1()
	elif args.stage == 2:
		if args.output and args.output != args.folder:
			args.folder = args.output
		stage2()
