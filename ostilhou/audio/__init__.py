
from typing import List

import subprocess
import json
import os.path
from os import listdir
from random import choice
from math import inf, ceil
from tempfile import NamedTemporaryFile

from pydub import AudioSegment
from pydub.utils import get_player_name
from pydub.generators import WhiteNoise
from pydub.silence import detect_nonsilent



def load_audiofile(path: str, sr=None) -> AudioSegment:
    data = AudioSegment.from_file(path)
    if isinstance(sr, int):
        data.set_channels(1)
        data.set_frame_rate(sr)
        data.set_sample_width(2)
    return data



def get_segment(i, song, segments):
    start = int(segments[i][0])
    stop = int(segments[i][1])
    seg = song[start: stop]
    return seg



def play_segment(i, song, segments, speed):
    play_with_ffplay(get_segment(i, song, segments), speed)



def get_audiofile_info(filename):
    r = subprocess.check_output(['ffprobe', '-hide_banner', '-v', 'panic', '-show_streams', '-of', 'json', filename])
    r = json.loads(r)
    return r['streams'][0]



def get_audiofile_length(filename):
    """
        Get audio file length in seconds
    """
    return float(get_audiofile_info(filename)['duration'])


    
def play_with_ffplay(seg, speed=1.0):
    with NamedTemporaryFile("w+b", suffix=".wav") as f:
        seg.export(f.name, "wav")
        player = get_player_name()
        p = subprocess.Popen(
            [player, "-nodisp", "-autoexit", "-loglevel", "quiet", "-af", f"atempo={speed}", f.name],
        )
        p.wait()



def convert_to_wav(src, dst, verbose=True, keep_orig=True):
    """
        Convert to 16kHz mono pcm
        Validate filename

        Parameters
        ----------
            verbose (bool):
                Info text to stdout
            keep_orig (bool):
                keep  original file (or rename if src and dst are the same)
    """
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    if src == dst:
        # Rename existing audio file
        rep, filename = os.path.split(src)
        basename, ext = os.path.splitext(filename)
        new_name = basename + "_orig" + ext
        new_src = os.path.join(rep, new_name)
        if verbose: print(f"AUDIO_CONV: renaming {filename} to {new_name}")
        os.rename(src, new_src)
        src = new_src

    if verbose:
        print(f"AUDIO_CONV: converting {src} to {dst}...")
    rep, filename = os.path.split(dst)
    dst = os.path.join(rep, filename)
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-i', src, '-acodec', 'pcm_s16le',
                     '-ac', '1', '-ar', '16000', dst])

    if not keep_orig:
        if verbose:
            print(f"AUDIO_CONV: Removing {src}")
        os.remove(src)



def convert_to_mp3(src, dst, verbose=True):
    """
        Convert to mp3
        Validate filename
    """
    if verbose:
        print(f"converting {src} to {dst}...")
    if os.path.abspath(src) == os.path.abspath(dst):
        print("ERROR: source and destination are the same, skipping")
        return -1
    rep, filename = os.path.split(dst)
    dst = os.path.join(rep, filename)
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-i', src,
                     '-ac', '1', dst])



def concatenate_audiofiles(file_list, out_filename, remove=False):
    """ Concatenate a list of audio files to a single audio file

        Parameters
        ----------
            remove (bool):
                remove original files
    """

    if len(file_list) <= 1:
        return
    
    file_list_filename = "audiofiles.txt"
    with open(file_list_filename, 'w') as f:
        f.write('\n'.join([f"file '{wav}'" for wav in file_list]))
    
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-f', 'concat',
                     '-safe', '0',
                     '-i', file_list_filename,
                     '-c', 'copy', out_filename])
    os.remove(file_list_filename)
    
    if remove:
        for fname in file_list:
            os.remove(fname)
    


def get_min_max_energy(segment: AudioSegment, chunk_size=100, overlap=50):
    """ Return the minimum dBFS of the segment, wich is above -inf.
        chunk_size and overlap in milliseconds
    """
    max_energy = -999
    energy_bins = dict()

    for i in range(0, len(segment), chunk_size-overlap):
        chunk = segment[i: i+chunk_size]  # Pydub will take care of overflow
        if chunk.dBFS == -inf:
            continue
        energy = round(chunk.dBFS)
        if energy in energy_bins:
            energy_bins[energy] += 1
        else:
            energy_bins[energy] = 1
        max_energy = max(max_energy, energy)
    
    bins_list = sorted(energy_bins.items())
    n_thresh = ceil(sum(energy_bins.values()) / 1000)

    for e, n in bins_list:
        if e <= -80: continue
        if n < n_thresh: continue
        min_energy = e
        break

    return min_energy, max_energy



def _recursive_split(song: AudioSegment, segment: list, max_length=15, min_silence_len=300):
    start, end = segment
    if (end-start) / 1000 < max_length:
        # Segment's length is short enough
        return [segment]

    min_e, max_e = get_min_max_energy(song[start:end])
    delta_e = max_e - min_e
    thresh = min_e + delta_e / 4.5
    sub_segments = detect_nonsilent(song[start:end], min_silence_len=min_silence_len, silence_thresh=thresh)

    # Filter out segments too short (< 0.8s)
    sub_segments = [ sub for sub in sub_segments if sub[1]-sub[0] > 800 ]

    if len(sub_segments) == 1:
        s, e = sub_segments[0]
        if e-s > max_length:
            # Sub divide a second time, if necessary
            min_e, max_e = get_min_max_energy(song[s:e])
            delta_e = max_e - min_e
            thresh = min_e + delta_e / 5
            sub2 = detect_nonsilent(song[s:e], min_silence_len=150, silence_thresh=thresh)
            return [ [start+s, start+e] for s, e in sub2 ]
        else:
            return [[start+s, start+e]]

    result = []
    for seg in sub_segments:
        result.extend(_recursive_split(song, [start + seg[0], start + seg[1]]))
    sub_segments = result

    return result



def split_to_segments(song: AudioSegment, max_length=15, min_length=5, min_silence_length=300) -> List:
    """
        Return a list of sub-segments from a pydub AudioSegment
        Sub-segments are represented as 2-elements lists:
            [start, end]
        Where 'start' and 'end' are in milliseconds
    """
    segments: list = _recursive_split(song, [0, len(song)], max_length=max_length, min_silence_len=min_silence_length)

    # Extend segments length
    for i, seg in enumerate(segments[1:]):
        prev = segments[i]
        gap = seg[0] - prev[1]
        if 100 < gap < 1000:
            prev[1] += gap // 2 - 50
            seg[0] -= gap // 2 - 50

    # Concatenate short segments
    result = [segments[0]]
    for i, seg in enumerate(segments[1:]):
        prev = segments[i]
        prev_length = prev[1]-prev[0]
        seg_length = seg[1]-seg[0]
        gap = seg[0] - prev[1]
        
        if gap < 500 and prev_length + seg_length < min_length*1000:
            # Extend previous segment with this segment
            result[-1][1] = seg[1]
        else:
            result.append(seg)

    return result



_AMB_REP = os.path.join(os.path.split(os.path.abspath(__file__))[0], "amb")
AUDIO_AMB_FILES = [os.path.abspath(os.path.join(_AMB_REP, f))
                    for f in listdir(_AMB_REP)
                    if f[-3:] in ("wav", "mp3")]


def add_amb_random(voice_file, output_file, gain=None):
    amb_file = choice(AUDIO_AMB_FILES)
    voice = AudioSegment.from_file(voice_file)
    amb = AudioSegment.from_file(amb_file)

    if gain:
        amb += gain
    elif amb.dBFS > -30: amb -= amb.dBFS + 30
    
    if voice.dBFS < -25: voice += -voice.dBFS - 20
    # print(amb_file, amb.rms, amb.dBFS)
    # print(voice_file, voice.rms, voice.dBFS)

    combined = voice.overlay(amb, loop=True)
    print("Exporting to", output_file)
    combined.export(output_file, format='wav', parameters=['-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000'])


def add_whitenoise(voice_file, output_file, gain=-20):
    voice = AudioSegment.from_file(voice_file)
    noise = WhiteNoise().to_audio_segment(duration=len(voice))
    noise += gain
    combined = voice.overlay(noise)
    print("Exporting to", output_file)
    combined.export(output_file, format='wav', parameters=['-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000'])
