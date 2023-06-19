from typing import List
import os
import sys
import subprocess
import json

from vosk import Model, KaldiRecognizer, SetLogLevel
from pydub import AudioSegment

from .post_processing import apply_post_process_dict_text, post_process_text, post_process_vosk
from ..text.inverse_normalizer import inverse_normalize_vosk



_vosk_loaded = False
MODEL_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '..', '..', '..', 'models'))
DEFAULT_MODEL = os.path.join(MODEL_DIR, "current")



def load_vosk(path: str = DEFAULT_MODEL) -> None:
    global recognizer
    global _vosk_loaded

    SetLogLevel(-1)
    model_path = os.path.normpath(path or DEFAULT_MODEL)
    print("Loading vosk model", model_path, file=sys.stderr)
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    _vosk_loaded = True



def transcribe_segment(segment: AudioSegment, normalize=False) -> str:
    if not _vosk_loaded:
        load_vosk()
    
    # seg = song[segments[idx][0]:segments[idx][1]]
    segment = segment.get_array_of_samples().tobytes()
    i = 0
    while i + 4000 < len(segment):
        recognizer.AcceptWaveform(segment[i:i+4000])
        i += 4000
    recognizer.AcceptWaveform(segment[i:])
    text = eval(recognizer.FinalResult())["text"]
    return apply_post_process_dict_text(text)



def transcribe_file(filepath: str, normalize=False) -> List[str]:

    def format_output(result, normalize=False):
        sentence = eval(result)["text"]
        sentence = post_process_text(sentence, normalize)
        return sentence

    if not _vosk_loaded:
        load_vosk()
    
    text = []

    with subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i",
                                filepath,
                                "-ar", "16000" , "-ac", "1", "-f", "s16le", "-"],
                                stdout=subprocess.PIPE) as process:

        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = format_output(recognizer.Result(), normalize)
                if result:
                    text.append(result)
        result = format_output(recognizer.FinalResult(), normalize)
        if result:
            text.append(result)
    
    return text



def transcribe_file_timecode(filepath: str, normalize=False) -> List[dict]:
    """ Return list of infered words with associated timecodes (vosk format)

        Parameters
            normalized (boolean): inverse-normalize sentences
    """

    def format_output(result, normalize=False) -> List[dict]:
        jres = json.loads(result)
        if not "result" in jres:
            return []
        words = jres["result"]
        words = post_process_vosk(words, normalize)
        return words

    if not _vosk_loaded:
        load_vosk()

    tokens = []
    with subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i",
                                filepath,
                                "-ar", "16000" , "-ac", "1", "-f", "s16le", "-"],
                                stdout=subprocess.PIPE) as process:

        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                tokens.extend(format_output(recognizer.Result(), normalize))
        tokens.extend(format_output(recognizer.FinalResult(), normalize))
    
    return tokens


# def sentence_post_process(text: str) -> str:
#     """ Add hyphens back to composite words and inverse-normalize text """

#     if not text:
#         return ''
    
#     # web adresses
#     if "HTTP" in text or "WWW" in text:
#         text = text.replace("pik", '.')
#         text = text.replace(' ', '')
#         return text.lower()
    
#     for sub in _postproc_sub:
#         text = text.replace(sub, _postproc_sub[sub])
    
#     splitted = text.split(maxsplit=1)
#     splitted[0] = splitted[0].capitalize()
#     return ' '.join(splitted)
