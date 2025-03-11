from importlib import resources

from ostilhou.audio.audio_numpy import split_to_segments, get_samples, binary_split
from ostilhou.asr.recognizer import transcribe_file_timecoded_callback_ffmpeg


def test_audio_numpy():
    audio_file = resources.files(__name__) / "27782.mp3"
    # audio_file = "/home/gweltaz/STT/aligned_test/" + "bali_breizh_poc'her1.wav"
    sample_rate = 4000
    samples = get_samples(audio_file, sample_rate, 4000)

    split = binary_split(samples)
    print(split)

    segments = split_to_segments(samples, sample_rate)

    print(len(samples) / sample_rate)
    print(segments)
