import numpy as np

from ostilhou.audio.ffmpeg import stream_audio_file


def get_samples(path: str, sample_rate=16000, buffer_size=8000) -> np.ndarray:
    """Returns a Numpy array of normalized float32 samples from an audio file."""
    chunks = []

    def handle_buffer(data):
        chunks.append(data)

    try:
        stream_audio_file(path, sample_rate, handle_buffer, buffer_size)
    except Exception as e:
        raise RuntimeError(f"Failed to stream audio file '{path}': {e}") from e

    if chunks:
        raw_data = b''.join(chunks)
        samples = np.frombuffer(raw_data, dtype=np.int16)
        normalized_samples = samples.astype(np.float32) / 32768.0
        return normalized_samples
    else:
        return np.array([], dtype=np.float32)



def _framed_rms(samples: np.ndarray, chunk_size: int, overlap: int) -> np.ndarray:
    """
    Vectorized framing + RMS computation.
    Returns one RMS energy value per frame.
    """
    step = chunk_size - overlap
    n = len(samples)
    if n == 0:
        return np.array([])

    # Pad so the last frame is a full chunk_size window (avoids a ragged
    # final frame skewing the energy stats).
    n_frames = max(1, int(np.ceil((n - chunk_size) / step)) + 1) if n > chunk_size else 1
    pad_len = max(0, (n_frames - 1) * step + chunk_size - n)
    padded = np.pad(samples, (0, pad_len))

    # Build overlapping frames
    frames = np.lib.stride_tricks.sliding_window_view(padded, chunk_size)[::step]

    rms = np.sqrt(np.mean(np.square(frames), axis=1))
    return rms


def get_min_max_energy(samples: np.ndarray, chunk_size: int, overlap: int):
    """Calculate minimum and maximum energy across the audio file."""
    energies = _framed_rms(samples, chunk_size, overlap)
    if energies.size == 0:
        return 0.0, 0.0
    return float(energies.min()), float(energies.max())


def binary_split(
    samples,
    sample_rate=16000,
    threshold_ratio=0.1,
    min_silence_duration: float = 0.2
) -> list:
    """Split audio at the quietest point.

    Args:
        samples: Audio samples
        threshold_ratio: Float, the ratio to determine threshold above min energy

    Returns:
        List of tuples with (start_sample, end_sample) ranges for each segment
    """
    chunk_size = int((100 / 1000) * sample_rate)  # 0.1s chunks
    overlap = int((50 / 1000) * sample_rate)  # 0.05s overlap
    step = chunk_size - overlap
    min_silence_samples = int(min_silence_duration * sample_rate)

    min_e, max_e = get_min_max_energy(samples, chunk_size, overlap)
    delta_e = max_e - min_e
    thresh = min_e + delta_e * threshold_ratio

    # Find segments above the energy threshold
    energies = _framed_rms(samples, chunk_size, overlap)
    segments = []
    seg_start = 0
    in_noisy_chunk = False

    for frame_idx, chunk_rms in enumerate(energies):
        i = frame_idx * step
        if chunk_rms >= thresh:
            if not in_noisy_chunk:
                seg_start = i
                in_noisy_chunk = True
        else:
            if in_noisy_chunk:
                segments.append((seg_start, min(i + chunk_size, len(samples))))
                in_noisy_chunk = False

    if in_noisy_chunk:
        segments.append((seg_start, len(samples)))

    if not segments:
        return segments

    # Find longest silence between segments
    max_sil_length = 0
    max_sil_length_idx = -1
    for i in range(1, len(segments)):
        sil_length = segments[i][0] - segments[i - 1][1]
        if sil_length >= min_silence_samples and sil_length > max_sil_length:
            max_sil_length = sil_length
            max_sil_length_idx = i

    if max_sil_length_idx > 0:
        left_seg = (segments[0][0], segments[max_sil_length_idx - 1][1])
        right_seg = (segments[max_sil_length_idx][0], segments[-1][1])
        return [left_seg, right_seg]

    # No usable silence gap was found. Split at the midpoint.
    mid = len(samples) // 2
    if mid == 0:
        return []  # segment too short to split further
    return [(0, mid), (mid, len(samples))]


def split_to_segments(
        audio_samples: np.ndarray,
        sample_rate: int,
        max_length: float = 10.0,
        threshold_ratio: float = 0.1,
        min_silence_duration: float = 0.2
    ) -> list:
    """
    Return a list of shorter sub-segments from an audio buffer.
    Sub-segments are represented as 2-elements lists [start, end]
    where 'start' and 'end' are in milliseconds.

    Args:
        max_length (float):
            sub-segments maximum length (in seconds)
        threshold_ratio (0.0 < float < 1.0):
            the silence threshold (depending on min/max energy of the audio segment)
        min_silence_duration (float):
            minimum silence gap (in seconds) required to be treated as a valid split point
    """
    audio_samples = audio_samples.astype(np.float64)
    segments_stack = [(0, len(audio_samples))]
    short_segments = []

    while segments_stack:
        segment = segments_stack.pop()
        start, end = segment
        seg_len = (end - start) / sample_rate

        if seg_len <= max_length:
            short_segments.append(segment)
            continue

        sub_segments = binary_split(
            audio_samples[start:end],
            sample_rate,
            threshold_ratio,
            min_silence_duration
        )

        if not sub_segments:
            # Could not split further (e.g. segment too short to bisect).
            # Keep the whole thing rather than silently dropping it.
            short_segments.append(segment)
            continue

        segments_stack.extend([(start + s, start + e) for s, e in sub_segments])

    short_segments = [(start / sample_rate, end / sample_rate) for start, end in short_segments]
    return sorted(short_segments)
