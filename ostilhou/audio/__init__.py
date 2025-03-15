from typing import List, Optional

import sys
from os import listdir
import os.path
import subprocess
import json
import array
from random import choice
from tempfile import NamedTemporaryFile

from colorama import Fore

from pydub import AudioSegment
from pydub.utils import get_player_name
from pydub.generators import WhiteNoise


AUDIO_FORMATS = ('wav', 'mp3', 'm4a', 'ogg', 'mp4', 'mkv')


def find_associated_audiofile(path: str, silent=False) -> Optional[str]:
    basename, _ = os.path.splitext(path)

    for ext in AUDIO_FORMATS:
        audio_path = os.path.extsep.join((basename, ext))
        if os.path.exists(audio_path):
            if not silent:
                print("Found audio file:", audio_path)
            return audio_path
    print(Fore.RED + f"Could not find {audio_path}" + Fore.RESET, file=sys.stderr)
    return None



def load_audiofile(path: str, sr=16000) -> AudioSegment:
    data = AudioSegment.from_file(path)
    data = prepare_segment_for_decoding(data)
    return data



def get_audio_segment(i, audio: AudioSegment, segments):
    """
    Args:
        i (int) : an index
        audio (AudioSegment)
        segments: list of tuple of floats (seconds)
    """
    start = int(segments[i][0] * 1000)
    stop = int(segments[i][1] * 1000)
    seg = audio[start: stop]
    return seg



def audio_segments(audio, segments):
    for start, stop in segments:
        yield audio[start, stop]



def prepare_segment_for_decoding(segment: AudioSegment) -> AudioSegment:
    """ Ensure that the segment is the right sampling rate and depth """

    if segment.channels > 1:
        segment = segment.set_channels(1)
    if segment.frame_rate != 16000:
        segment = segment.set_frame_rate(16000)
    if segment.sample_width != 2:
        segment = segment.set_sample_width(2)
    return segment



def play_audio_segment(i, song, segments, speed):
    play_with_ffplay(get_audio_segment(i, song, segments), speed)



def get_audiofile_info(filename) -> dict:
    r = subprocess.check_output(['ffprobe', '-hide_banner', '-v', 'panic', '-show_streams', '-of', 'json', filename])
    r = json.loads(r)
    return r['streams'][0]



def get_audiofile_length(filename) -> float:
    """ Get audio file length in seconds """
    info = get_audiofile_info(filename)
    if "duration" in info:
        return float(info["duration"])
    elif "tags" in info:
        # For MKV files
        h, m, s = info["tags"]["DURATION"].split(':')
        return float(h) * 3600 + float(m) * 60 + float(s)



def is_audiofile_valid_format(filename) -> bool:
    """ Returns True if audio file is 16KHz s16le PCM """
    info = get_audiofile_info(filename)
    if info["codec_name"] != "pcm_s16le":
        return False
    if info["sample_rate"] != "16000":
        return False
    if info["channels"] != 1:
        return False
    return True


    
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
        Convert to 16kHz s16le mono PCM

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
        # Rename original audio file (to keep it)
        rep, filename = os.path.split(src)
        basename, ext = os.path.splitext(filename)
        new_name = basename + "_orig" + ext
        new_src = os.path.join(rep, new_name)
        if verbose: print(Fore.YELLOW + f"AUDIO_CONV: renaming {filename} to {new_name}" + Fore.RESET)
        os.rename(src, new_src)
        src = new_src

    if verbose:
        print(Fore.YELLOW + f"AUDIO_CONV: converting '{src}' to '{dst}'..." + Fore.RESET)
    rep, filename = os.path.split(dst)
    dst = os.path.join(rep, filename)
    subprocess.call([
            'ffmpeg', '-v',
            'panic',
            '-i', src,
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            dst
        ])

    if not keep_orig:
        if verbose:
            print(Fore.YELLOW + f"AUDIO_CONV: Removing {src}" + Fore.RESET)
        os.remove(src)



def convert_to_mp3(src, dst, verbose=True, keep_orig=True):
    """ Convert to MP3 """
    if verbose:
        print(Fore.YELLOW + f"AUDIO_CONV: converting '{src}' to '{dst}'..." + Fore.RESET)
        
    if os.path.abspath(src) == os.path.abspath(dst):
        print(Fore.RED + "ERROR: source and destination are the same, skipping" + Fore.RESET)
        return -1
    rep, filename = os.path.split(dst)
    dst = os.path.join(rep, filename)
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-i', src,
                     '-ac', '1', dst])
    
    if not keep_orig:
        if verbose:
            print(Fore.YELLOW + f"AUDIO_CONV: Removing {src}")
        os.remove(src)



def concatenate_audiofiles(file_list, out_filename, remove=False):
    """
    Concatenate a list of audio files to a single audio file

    Parameters
    ----------
        remove (bool):
            remove original files
    """

    if len(file_list) <= 1:
        return
    
    file_list_filename = "audiofiles.txt"
    with open(file_list_filename, 'w', encoding='utf-8') as f:
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



def export_segment(audio_path: str, start: float, end: float, new_path: str):
    """
    Split an audiofile in many segments

    Arguments:
        audio_path (str): the path of the original audiofile
        start (float) : time offset of beginning of segment
        end (float) : time offset of end of segment
        new_path (str): path of output file
    """
    # Cut the audio into segments using FFmpeg and suppress output
    subprocess.run([
        "ffmpeg",
        "-i", audio_path,
        "-ss", str(start),
        "-to", str(end),
        "-c", "copy", # Write using the same codec
        new_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



_AMB_REP = os.path.join(os.path.split(os.path.abspath(__file__))[0], "amb")
if os.path.exists(_AMB_REP):
    AUDIO_AMB_FILES = [os.path.abspath(os.path.join(_AMB_REP, f))
                        for f in listdir(_AMB_REP)
                        if f[-3:] in ("wav", "mp3")]
else:
    print("Empty 'amb' folder (samples of ambient audio)", file=sys.stderr)



def add_random_amb_noise(voice_file, output_file, gain=None):
    """
    Add random ambient noises to a voice audio segment
    Export to 16kHz s16le PCM
    """
    voice = AudioSegment.from_file(voice_file)
    combined_amb = AudioSegment.silent(duration=0)
    
    while len(combined_amb) < len(voice):
        amb_file = choice(AUDIO_AMB_FILES)
        amb = AudioSegment.from_file(amb_file)
        
        if gain:
            amb += gain
        elif amb.dBFS > -30:
            amb -= amb.dBFS + 30
            
        combined_amb += amb
    
    combined_amb = combined_amb[:len(voice)]
    
    if voice.dBFS < -25: voice += -voice.dBFS - 20
    # print(amb_file, amb.rms, amb.dBFS)
    # print(voice_file, voice.rms, voice.dBFS)

    combined = voice.overlay(combined_amb)
    print("Exporting to", output_file)
    combined.export(
        output_file,
        format='wav',
        parameters=['-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000']
    )



def add_whitenoise(voice_file, output_file, gain=-20):
    voice = AudioSegment.from_file(voice_file)
    noise = WhiteNoise().to_audio_segment(duration=len(voice))
    noise += gain
    combined = voice.overlay(noise)
    print("Exporting to", output_file)
    combined.export(output_file, format='wav', parameters=['-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000'])


def get_audio_samples(filepath: str, sample_rate: int):
    # Configure ffmpeg command to convert audio to required format
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', filepath,
        '-ar', str(sample_rate),       # 8kHz sample rate
        '-ac', '1',          # Mono
        '-f', 's16le',       # 16-bit signed little-endian PCM
        '-',                 # Output to stdout
        '-loglevel', 'error' # Reduce ffmpeg output
    ]
    
    # Run ffmpeg as subprocess and capture output
    process = subprocess.Popen(
        ffmpeg_cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Read all audio data
    stdout_data, stderr_data = process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr_data.decode() if stderr_data else "Unknown error"
        raise RuntimeError(f"ffmpeg conversion failed: {error_msg}")
    
    # Convert raw bytes to array of 16-bit samples
    audio_data = array.array('h')  # 'h' is for signed short (16-bit) values
    audio_data.frombytes(stdout_data)
    
    # Create normalized samples (float values between -1 and 1)
    sample_max = 2**(16-1)  # For 16-bit audio, max value is 2^15
    normalized_samples = [s/sample_max for s in audio_data]
    
    return normalized_samples