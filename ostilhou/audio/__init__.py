
from os import listdir
import os.path
from random import choice
from pydub import AudioSegment
from pydub.utils import get_player_name
from tempfile import NamedTemporaryFile
import subprocess
import json



def load_audiofile(path: str) -> AudioSegment:
    return AudioSegment.from_file(path)


def get_segment(i, song, segments):
    start = int(segments[i][0])
    stop = int(segments[i][1])
    seg = song[start: stop]
    return seg



_AMB_REP = os.path.join(os.path.split(os.path.abspath(__file__))[0], "amb")
AUDIO_AMB_FILES = [os.path.abspath(os.path.join(_AMB_REP, f))
                    for f in listdir(_AMB_REP)
                    if f[-3:] in ("wav", "mp3")]


def add_amb_random(voice_file, output_file):
    amb_file = choice(AUDIO_AMB_FILES)
    voice = AudioSegment.from_file(voice_file)
    amb = AudioSegment.from_file(amb_file)

    if amb.dBFS > -30: amb -= amb.dBFS + 30
    if voice.dBFS < -25: voice += -voice.dBFS - 20
    # print(amb_file, amb.rms, amb.dBFS)
    # print(voice_file, voice.rms, voice.dBFS)

    combined = voice.overlay(amb, loop=True)
    print("Exporting to", output_file)
    combined.export(output_file, format='wav', parameters=['-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000'])



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
        print(p)
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