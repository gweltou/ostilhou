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

import argparse

from ostilhou.audio import convert_to_wav
from ostilhou.asr import load_segments_data
from srt2split import srt2split



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('folder')
	parser.add_argument('-o', '--output', type=str, help="Destination folder")
	parser.add_argument('--remove', action='store_true', help="Remove original files (audio and subs)")
	args = parser.parse_args()

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
		
		srt2split(new_file)

		# Remove subtitle file if necessary
		if args.output and args.output != args.folder:
			os.remove(new_file)
		
		# Clean files
		segments = load_segments_data(wav_file.replace(".wav", ".split"))
		text = load_text_data(wav_file.replace(".wav", ".txt"))
