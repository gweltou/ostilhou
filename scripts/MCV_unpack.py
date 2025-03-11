#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Author:        Gweltaz Duval-Guennoc
 
    Unpack Mozilla's Common Voice dataset and prepare data
    to be used for Kaldi framework.
    
    usage:
        $ python3 unpack.py train.tsv train
        $ python3 unpack.py test.tsv test
"""


import sys
import os
import shutil
import tarfile
from math import floor, ceil
from pydub import AudioSegment

from ostilhou.asr import load_segments_data
from ostilhou.asr.dataset import create_ali_file
from ostilhou.audio import play_audio_segment, convert_to_wav, get_audiofile_length, concatenate_audiofiles



spk2gender_file = "spk2gender"
blacklisted_speakers_file = "blacklisted_speakers.txt"
blacklisted_sentences_file = "blacklisted_sentences.txt"

prescoring_file = "mcv13-br_score_all.tsv"
USE_PRESCORING = False    # Set to True if you want to use the prescoring_file to filter out sentences from the dataset
EXCLUDE_FROM_LM = False



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} data_file.tsv [data_file2.tsv...] SAVE_FOLDER")
        sys.exit(1)
    
    # Extract archive
    tar_file = [f for f in os.listdir() if f.endswith(".tar.gz")][0]
    with tarfile.open(tar_file, 'r') as tar:
        f = next(filter(lambda x: x.endswith(".tsv"), tar.getnames()))
        data_folder = os.path.split(f)[0]
        if not os.path.exists(data_folder):
            # Untar archive
            tar.extractall()
            #os.system("tar xvf cv-corpus-*-br.tar.gz")
    print(data_folder)
    
    # Genders
    speakers_gender = dict()
    if os.path.exists(spk2gender_file):
        with open(spk2gender_file, 'r') as f:
            for l in f.readlines():
                speaker, gender = l.split()
                speakers_gender[speaker] = gender
    else:
        print("spk2gender file not found")
    
    # Don't use data from those speakers
    blacklisted_speakers = []
    if os.path.exists(blacklisted_speakers_file):
        with open(blacklisted_speakers_file, 'r') as f:
            blacklisted_speakers = [l.split()[0] for l in f.readlines() if not l.startswith('#')]
    else:
        print("Blacklisted speakers file not found")
   
    # Avoid those sentences
    blacklisted_sentences = []
    if os.path.exists(blacklisted_sentences_file):
        with open(blacklisted_sentences_file, 'r') as f:
            blacklisted_sentences = [l.strip() for l in f.readlines() if not l.startswith('#')]
    else:
        print("Blacklisted sentences file not found")
    
    
    if USE_PRESCORING:
        valid_utterances = set()
        with open(prescoring_file, 'r') as f:
            f.readline()    # Skip header
            n = 0
            for l in f.readlines():
                n += 1
                l = l.split('\t')
                WER = float(l[1])
                CER = float(l[2])
                if WER < 1.0 and CER < 0.8:
                    valid_utterances.add(l[0])
        print("Number of validated utterances by prescoring:", 100*len(valid_utterances)/n)
    
    
    dest_folder = sys.argv[-1]
    data_files = sys.argv[1:-1]
    
    clips_folder = os.path.join(data_folder, "clips")
    ungendered_speakers = set()
    parsed_audiofiles = set()   # To make sure every utterance is used only once in datasets
    num_kept = 0
    
    if not os.path.exists(dest_folder):
        os.mkdir(dest_folder)
    
    if not os.path.exists("discarded"):
        os.mkdir("discarded")
    
    for data_file in data_files:
        data = []
        cumul_time = 0.0
        
        data_file = os.path.join(data_folder, data_file)
        print(data_file)
        if os.path.exists(data_file):
            # Old format:
            # client_id, path, sentence, up_votes, down_votes, age, gender, accent
            # New format:
            # client_id, path, sentence_id, sentence, ?, up_votes, down_votes, age, gender, accent, variant,...
            with open(data_file, 'r') as f:
                f.readline() # skip header
                l = f.readline().strip()
                while l:
                    l = l.split('\t')
                    l[0] = l[0]
                    data.append(l[:9])  # Keep first 8 fields only
                    l = f.readline().strip()
        else:
            print("File not found:", data_file)
            continue
        
        speakers = set([l[0] for l in data])
        print(f"{len(speakers)} speakers found...")
        
        for speaker in speakers:
            # for each speaker, create a folder an concatenate each of its utterances in one audio file
            
            discard = speaker in blacklisted_speakers
            if discard:
                print("(discarded)", end=' ')
            
            print(speaker, end=' ')
            
            if discard:
                speaker_folder = os.path.join("discarded", speaker)
            else:
                speaker_folder = os.path.join(dest_folder, speaker)
                
            wav_concat = os.path.join(speaker_folder, speaker+'.wav')
            if os.path.exists(wav_concat):
                # Speaker has already been parsed
                print('(already done) |')
                if not discard:
                    l = get_audiofile_length(wav_concat)
                    cumul_time += l
                continue
            
            utterances = [utt for utt in data if utt[0] == speaker]
            
            if speaker not in speakers_gender:
                if utterances[0][8] in ('female', 'male'):
                    speakers_gender[speaker] = utterances[0][8][0]
                elif not discard:
                    ungendered_speakers.add(speaker)
            
            audiofiles = []
            text = []
            segments = []
            t = 0.0
            for utt in utterances:
                if utt[1] in parsed_audiofiles:
                    print("already seen:", utt)
                else:
                    parsed_audiofiles.add(utt[1])
                
                if utt[3] in blacklisted_sentences:
                    print('B', end='')
                    continue
                
                if USE_PRESCORING and utt[1] not in valid_utterances:
                    print('x', end='')
                    # Move to a special folder
                    src = os.path.join(clips_folder, utt[1])
                    dst = os.path.join("discarded", speaker)
                    if not os.path.exists(dst):
                        os.mkdir(dst)
                    shutil.copy(src, dst)
                    continue
                
                num_kept += 1
                
                wav = utt[1].replace('.mp3', '.wav')
                src = os.path.join(clips_folder, utt[1])
                dst = os.path.join(speaker_folder, wav)
                # Convert to wav
                if not os.path.exists(dst):
                    if not os.path.exists(speaker_folder):
                        os.mkdir(speaker_folder)
                    convert_to_wav(src, dst, verbose=False)
                nt = t + get_audiofile_length(dst)
                segments.append((t, nt)) # Offset end of segment by a 0.2 second
                t = nt
                audiofiles.append(dst)
                text.append(utt[3])
                print('.', end='', flush=True)
                
            cumul_time += t
            
            if not text:
                print('|')
                continue
            
            # Concatenate audio files of the same speaker
            if len(audiofiles) == 1:
                os.rename(audiofiles[0], wav_concat)
            else:
                concatenate_audiofiles(audiofiles, wav_concat, remove=True)
            
            ali_path = os.path.join(speaker_folder, speaker + ".ali")
            create_ali_file(text, segments, ali_path,
                    audio_path=speaker + ".wav",
                    licence="CC0",
                    tags="MCV",
                    speaker=speaker,
                    gender=speakers_gender[speaker] if speaker in speakers_gender else 'u',
                )
            
            print('|')
    
        minutes, seconds = divmod(round(cumul_time), 60)
        hours, minutes = divmod(minutes, 60)
        print(f"Total clip time kept: {hours}h {minutes}' {seconds}''")
        print(f"Total utterance kept: {num_kept} ({num_kept/len(parsed_audiofiles):.2%})")
    
    
    # Categorize speakers of unknown gender
    # (this will help us measure the gender bias more precisely later)
    for speaker in ungendered_speakers:
        speaker_folder = os.path.join(dest_folder, speaker)
        split_file = os.path.join(speaker_folder, speaker+".split")
        segments = load_segments_data(split_file)
        wav_filename = os.path.join(speaker_folder, speaker+'.wav')
        song = AudioSegment.from_wav(wav_filename)
        gender = ''
        i = 0
        while gender not in ('m', 'f', 'u', 'x'):
            play_audio_segment(i, song, segments, 1.0)
            print("(Press 'u' for unknown, 'x' to skip this process or any other key to listen again)")
            gender = input(f"{speaker} Male or Female (m/f) ? ").lower()
            i = (i+1) % len(segments)
            if gender in ('m', 'f'):
                speakers_gender[speaker] = gender
        
        if gender == 'x':
            break
        
    
    # spk2gender file
    previous_speakers = []
    if os.path.exists(spk2gender_file):
        with open(spk2gender_file, 'r') as f:
            previous_speakers = [l.split()[0] for l in f.readlines()]
    
    with open(spk2gender_file, 'a') as f:
        for speaker in speakers_gender:
            if speaker not in previous_speakers:
                f.write(f"{speaker}\t{speakers_gender[speaker]}\n") 
