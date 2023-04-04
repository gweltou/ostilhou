
from os import listdir
import os.path
from pydub import AudioSegment
from random import choice



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

