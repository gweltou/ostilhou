
from pydub import AudioSegment
from pydub.utils import get_player_name
from pydub.generators import WhiteNoise



def get_min_max_energy(segment: AudioSegment, chunk_size=100, overlap=50):
    """Return the min and max RMS energy value for this audio segment"""
    min_energy = segment.max_possible_amplitude
    max_energy = 0
    for i in range(0, len(segment), chunk_size-overlap):
        chunk = segment[i: i+chunk_size]  # Pydub will take care of overflow
        mean = chunk.rms
        if mean < min_energy:
            min_energy = mean
        if mean > max_energy:
            max_energy = mean
    return (min_energy, max_energy)



def binary_split(audio: AudioSegment, treshold_ratio=0.1):
    """
    Split audio at the quietest point.
    """
    min_e, max_e = get_min_max_energy(audio)
    delta_e = max_e - min_e
    thresh = min_e + delta_e * treshold_ratio

    # Find segments above the energy threshold
    chunk_size = 100 # millisec
    overlap = 50 # millisec
    segments = []
    seg_start = 0 # millisec
    in_noisy_chunk = False
    
    for i in range(0, len(audio), chunk_size-overlap):
        chunk = audio[i: i+chunk_size]  # Pydub will take care of overflow
        if chunk.rms >= thresh:
            if not in_noisy_chunk:
                seg_start = i
                in_noisy_chunk = True
        else:
            if in_noisy_chunk:
                segments.append((seg_start, i+chunk_size))
                in_noisy_chunk = False
    if in_noisy_chunk:
        segments.append((seg_start, len(audio)))

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



def split_to_segments(audio: AudioSegment, max_length=10, threshold_ratio=0.1) -> list:
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
    segments_stack = [(0, len(audio))]
    short_segments = []

    while segments_stack:
        segment = segments_stack.pop()
        start, end = segment
        seg_len = end - start
        if seg_len <= max_length * 1000:
            short_segments.append(segment)
            continue
        sub_segments = binary_split(audio[start:end], threshold_ratio)
        segments_stack.extend([ (start + s, start + e) for s, e in sub_segments ])
    
    return sorted(short_segments)