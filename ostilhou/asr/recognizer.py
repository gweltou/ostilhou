from typing import List
import os
import sys
import subprocess
import json

from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from tqdm import tqdm

from .models import load_model
from ..audio import get_audiofile_length




def transcribe_segment(segment: AudioSegment) -> str:
    """ Transcribe a short AudioSegment """
    assert segment.frame_rate == 16000, f"Wrong sample rate {segment.frame_rate=}"
    assert segment.sample_width == 2, f"Wrong sample width {segment.sample_width=}"
    assert segment.channels == 1, f"Wrong number of channels {segment.channels=}"

    model = load_model()
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    
    data = segment.raw_data
    text = []
    i = 0
    while i + 4000 < len(data):
        if recognizer.AcceptWaveform(data[i:i+4000]):
            text.append(json.loads(recognizer.Result())["text"])
        i += 4000
    recognizer.AcceptWaveform(data[i:])
    text.append(json.loads(recognizer.FinalResult())["text"])

    return text



def transcribe_segment_ffmpeg(
    input_file: str, 
    start_time: float, 
    duration: float,
    model=None
) -> str:
    """ 
    Transcribe a segment of an audio file by streaming from ffmpeg to Vosk
    
    Args:
        input_file: Path to the audio file
        start_time: Start time in seconds
        duration: Duration of segment in seconds
        model: Optional pre-loaded Vosk model (will load default if None)
        
    Returns:
        Transcribed text from the segment
    """
    from vosk import Model, KaldiRecognizer
    
    # Load model if not provided
    if model is None:
        model = load_model()
    
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    
    # Configure ffmpeg to output raw audio in the format we need
    ffmpeg_cmd = [
        'ffmpeg',
        '-loglevel', 'error',  # Reduce ffmpeg output
        '-hide_banner',
        '-i', input_file,
        '-ss', str(start_time),
        '-t', str(duration),
        '-ar', '16000',  # 16kHz sample rate
        '-ac', '1',      # Mono
        '-f', 's16le',   # 16-bit signed little-endian PCM
        '-',             # Output to stdout
    ]
    
    # Start ffmpeg process and read its output
    process = subprocess.Popen(
        ffmpeg_cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    text = []
    chunk_size = 4000  # Same chunk size as original function
    
    # Process the audio stream in chunks
    while True:
        data = process.stdout.read(chunk_size)
        if len(data) == 0:
            break
            
        if recognizer.AcceptWaveform(data):
            text.append(json.loads(recognizer.Result())["text"])
    
    # Get final result and clean up
    text.append(json.loads(recognizer.FinalResult())["text"])
    
    # Ensure the process is terminated properly
    process.terminate()
    process.wait()
    
    # Check for any stderr output from ffmpeg
    error = process.stderr.read()
    if error and len(error) > 0:
        print(f"ffmpeg warning/error: {error.decode()}")
    
    return text



def transcribe_file_timecoded_callback_ffmpeg(
    input_file: str,
    callback: callable,
    model=None
):
    """ 
    Transcribe a segment of an audio file by streaming from ffmpeg to Vosk
    
    Args:
        input_file: Path to the audio file
        start_time: Start time in seconds
        duration: Duration of segment in seconds
        model: Optional pre-loaded Vosk model (will load default if None)
        
    Returns:
        Transcribed text from the segment
    """
    from vosk import Model, KaldiRecognizer
    
    # Load model if not provided
    if model is None:
        model = load_model()
    
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    
    # Configure ffmpeg to output raw audio in the format we need
    ffmpeg_cmd = [
        "ffmpeg",
        "-loglevel", "error",  # Reduce ffmpeg output
        "-hide_banner",
        "-i", input_file,
        "-ar", "16000",  # 16kHz sample rate
        "-ac", "1",      # Mono
        "-f", "s16le",   # 16-bit signed little-endian PCM
        "-",             # Output to stdout
    ]
    
    # Start ffmpeg process and read its output
    process = subprocess.Popen(
        ffmpeg_cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    chunk_size = 4000  # Same chunk size as original function
    
    # Process the audio stream in chunks
    while True:
        data = process.stdout.read(chunk_size)
        if len(data) == 0:
            break
            
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if "result" in result:
                callback(result["result"])
    
    # Get final result and clean up
    result = json.loads(recognizer.FinalResult())
    if "result" in result:
        callback(result["result"])
    
    # Ensure the process is terminated properly
    process.terminate()
    process.wait()
    
    # Check for any stderr output from ffmpeg
    error = process.stderr.read()
    if error and len(error) > 0:
        print(f"ffmpeg warning/error: {error.decode()}")



def transcribe_segment_timecoded(segment: AudioSegment) -> List[dict]:
    """ Transcribe a short AudioSegment, keeping the timecodes

        The resulting transcription is a list of Vosk tokens
        Each Vosk token is a dictionary of the form:
            {'word': str, 'start': float, 'end': float, 'conf': float}
        'start' and 'end' keys are in seconds
        'conf' is a normalized confidence score
    """
    assert segment.frame_rate == 16000
    assert segment.sample_width == 2
    assert segment.channels == 1
    
    model = load_model()
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    
    data = segment.get_array_of_samples().tobytes()
    timecoded_text = []
    i = 0
    while i + 4000 < len(data):
        if recognizer.AcceptWaveform(data[i:i+4000]):
            result = json.loads(recognizer.Result())
            if "result" in result:
                timecoded_text.extend(result["result"])
        i += 4000
    recognizer.AcceptWaveform(data[i:])
    result = json.loads(recognizer.FinalResult())
    if "result" in result:
        timecoded_text.extend(result["result"])
    return timecoded_text



def transcribe_segment_timecoded_callback(segment: AudioSegment, callback: callable):
    """ Transcribe a short AudioSegment, keeping the timecodes,
        Send result to callback function for every detected utterances

        The resulting transcription is a list of Vosk tokens
        Each Vosk token is a dictionary of the form:
            {'word': str, 'start': float, 'end': float, 'conf': float}
        'start' and 'end' keys are in seconds
        'conf' is a normalized confidence score
    """
    assert segment.frame_rate == 16000, f"Wrong sampling rate {segment.frame_rate=} (should be 16000)"
    assert segment.sample_width == 2, f"Wrong sample width {segment.sample_width=} (should be 2)"
    assert segment.channels == 1, f"Wrong number of channels {segment.channels=} (should be 1)"
    
    model = load_model()
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    
    data = segment.get_array_of_samples().tobytes()
    i = 0
    while i + 4000 < len(data):
        if recognizer.AcceptWaveform(data[i:i+4000]):
            result = json.loads(recognizer.Result())
            if "result" in result:
                callback(result["result"])
        i += 4000
    recognizer.AcceptWaveform(data[i:])
    result = json.loads(recognizer.FinalResult())
    if "result" in result:
        callback(result["result"])



def transcribe_file(filepath: str) -> List[str]:
    if not os.path.exists(filepath):
        print("Couldn't find {}".format(filepath), file=sys.stderr)

    model = load_model()
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    
    text = []

    with subprocess.Popen([
                            "ffmpeg",
                            "-loglevel", "quiet",
                            "-hide_banner",
                            "-i", filepath,
                            "-ar", "16000",
                            "-ac", "1",
                            "-f", "s16le",
                            "-"],
                            stdout=subprocess.PIPE) as process:

        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                sentence = json.loads(recognizer.Result())["text"]
                if sentence:
                    text.append(sentence)
        sentence = json.loads(recognizer.FinalResult())["text"]
        if sentence:
            text.append(sentence)
    
    return text



def transcribe_file_timecoded(filepath: str, show_progress_bar=True) -> List[dict]:
    """ Return a list of decoded words with timecodes (vosk format)

        The resulting transcription is a list of Vosk tokens.
        Each Vosk token is a dictionary in the form:
            {'word': str, 'start': float, 'end': float, 'conf': float}
        where:
            'start' and 'end' are in seconds
            'conf' is a normalized confidence score (between 0.0 and 1.0)
    """

    def format_output(result) -> List[dict]:
        jres = json.loads(result)
        return jres.get("result", [])
    
    if not os.path.exists(filepath):
        print("Couldn't find {}".format(filepath), file=sys.stderr)

    model = load_model()
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)

    total_duration = get_audiofile_length(filepath)
    progress = 0.0

    if show_progress_bar:
        progress_bar = tqdm(total=total_duration, unit='s', unit_scale=True)
    
    tokens = []
    with subprocess.Popen(
        [
            "ffmpeg",
            "-loglevel", "quiet",
            "-hide_banner",
            "-i", filepath,
            "-ar", "16000",
            "-ac", "1",
            "-f", "s16le",
            "-"
        ], stdout=subprocess.PIPE) as process:

        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                tokens.extend(format_output(recognizer.Result()))

            progress += (len(data) // 2) / 16000

            if show_progress_bar:
                progress_bar.n = min(progress, total_duration)
                progress_bar.refresh()
        
        tokens.extend(format_output(recognizer.FinalResult()))
    
    if show_progress_bar:
        progress_bar.close()
    
    return tokens
