from vosk import Model, KaldiRecognizer, SetLogLevel
from . import sentence_post_process


_vosk_loaded = False

ROOT = ""


def load_vosk():
    import os
    from vosk import Model, KaldiRecognizer, SetLogLevel

    
    global recognizer
    global _vosk_loaded

    SetLogLevel(-1)
    model = Model(os.path.normpath(os.path.join(ROOT, "../models/current")))
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    _vosk_loaded = True


def transcribe_segment(segment):
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
    return sentence_post_process(text)