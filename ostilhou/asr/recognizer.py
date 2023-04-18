import os
# from typing import List
from vosk import Model, KaldiRecognizer, SetLogLevel
from .post_processing import apply_post_process_dict_text
from ..text.inverse_normalizer import inverse_normalize_vosk



_vosk_loaded = False
ROOT = ""

def load_vosk():
    global recognizer
    global _vosk_loaded

    SetLogLevel(-1)
    model = Model(os.path.normpath(os.path.join(ROOT, "../models/current")))
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    _vosk_loaded = True



def transcribe_segment(segment, normalize=False):
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
