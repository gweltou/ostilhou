import numpy as np

from ostilhou.audio.ffmpeg import stream_audio_file



def get_samples(path: str, sample_rate=16000, buffer_size=8000):
    """Returns a Numpy array of int16 samples from an audio file"""
    chunks = []

    def handle_buffer(data):
        chunks.append(data)

    stream_audio_file(path, sample_rate, handle_buffer, buffer_size)

    if chunks:
        raw_data = b''.join(chunks)
        samples = np.frombuffer(raw_data, dtype=np.int16)
        return samples
    else:
        return np.array([], dtype=np.int16)



def get_min_max_energy(samples, chunk_size=100, overlap=50):
        """Calculate minimum and maximum energy across the audio file."""
        energies = []
    
        for i in range(0, len(samples), chunk_size-overlap):
            end = min(i + chunk_size, len(samples))
            chunk = samples[i:end]
            if len(chunk) > 0:
                rms = np.sqrt(np.mean(np.square(chunk)))
                energies.append(rms)
        
        if not energies:
            return 0, 0
                
        return min(energies), max(energies)


def binary_split(samples, sample_rate=16000, threshold_ratio=0.1) -> list:
    """
    Split audio at the quietest point.
    
    Parameters:
    - samples: Audio samples
    - threshold_ratio: Float, the ratio to determine threshold above min energy
    
    Returns:
    - List of tuples with (start_sample, end_sample) ranges for each segment
    """
    min_e, max_e = get_min_max_energy(samples)
    delta_e = max_e - min_e
    thresh = min_e + delta_e * threshold_ratio

    # Find segments above the energy threshold
    chunk_size: int = int((100 / 1000) * sample_rate)
    overlap: int = int((50 / 1000) * sample_rate)
    segments = []
    seg_start: int = 0
    in_noisy_chunk = False
    
    for i in range(0, len(samples), chunk_size - overlap):
        # Calculate RMS for this chunk
        chunk_rms = np.sqrt(np.mean(np.square(samples[i:i+chunk_size])))
        
        if chunk_rms >= thresh:
            if not in_noisy_chunk:
                seg_start = i
                in_noisy_chunk = True
        else:
            if in_noisy_chunk:
                segments.append((seg_start, i + chunk_size))
                in_noisy_chunk = False
                
    if in_noisy_chunk:
        segments.append((seg_start, len(samples)))

    if not segments:
        return segments
        
    # Find longest silence between segments
    max_sil_length = 0
    max_sil_length_idx = -1
    for i in range(1, len(segments)):
        sil_length = segments[i][0] - segments[i-1][1]
        if sil_length > max_sil_length:
            max_sil_length = sil_length
            max_sil_length_idx = i

    if max_sil_length_idx > 0:
        left_seg = (segments[0][0], segments[max_sil_length_idx-1][1])
        right_seg = (segments[max_sil_length_idx][0], segments[-1][1])
        return [left_seg, right_seg]
    return []



def split_to_segments(
        audio_samples: np.ndarray,
        sample_rate,
        max_length=10,
        threshold_ratio=0.1
    ) -> list:
    """
    Return a list of shorter sub-segments from a pydub AudioSegment.

    Sub-segments are represented as 2-elements lists [start, end]
    where 'start' and 'end' are in milliseconds.

    Args:
        max_length (float):
            sub-segments maximum length (in seconds)
        threshold_ratio (0.0 < float < 1.0):
            the silence threshold (depending on min/max energy of the audio segment)
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
        sub_segments = binary_split(audio_samples[start:end], sample_rate, threshold_ratio)
        segments_stack.extend([ (start + s, start + e) for s, e in sub_segments ])
    
    short_segments = [(start/sample_rate, end/sample_rate) for start, end in short_segments ]
    return sorted(short_segments)
