"""
    Coded with Claude 3.5 Sonnet (new)
"""


import numpy as np
import wave
import sys

from ostilhou.audio import load_audiofile



def save_wave(file_path, audio_data, sample_rate):
    """
    Save audio data to a WAV file using built-in wave module
    """
    # Convert to int16
    audio_data = np.int16(audio_data * 32767)
    
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())


def convolve_fft(signal, impulse_response):
    """
    Implement convolution using FFT for better performance
    """
    # Get the next power of 2 for optimal FFT performance
    N = len(signal) + len(impulse_response) - 1
    N_padded = 2 ** np.ceil(np.log2(N)).astype(int)
    
    # Compute FFTs
    signal_fft = np.fft.fft(signal, n=N_padded)
    ir_fft = np.fft.fft(impulse_response, n=N_padded)
    
    # Multiply in frequency domain
    result_fft = signal_fft * ir_fft
    
    # Inverse FFT and take real part
    result = np.real(np.fft.ifft(result_fft))
    
    # Trim to the correct length
    result = result[:len(signal)]
    
    return result


def normalize_audio(audio_data):
    """
    Normalize audio data to range [-1, 1]
    """
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        return audio_data / max_val
    return audio_data


def apply_reverb(dry_signal, impulse_response):
    """
    Apply convolution reverb to an audio signal using an impulse response
    """
    # Normalize inputs
    dry_signal = normalize_audio(dry_signal)
    impulse_response = normalize_audio(impulse_response)
    
    # Apply convolution
    wet_signal = convolve_fft(dry_signal, impulse_response)
    
    # Normalize output
    wet_signal = normalize_audio(wet_signal)
    
    return wet_signal


def mix_dry_wet(dry_signal, wet_signal, mix_ratio=0.7):
    """
    Mix the dry and wet signals according to the mix ratio
    mix_ratio: 0 = dry only, 1 = wet only
    """
    return (1 - mix_ratio) * dry_signal + mix_ratio * wet_signal


def process_audio_with_reverb(input_path, ir_path, output_path, mix_ratio=0.7):
    """
    Process an audio file with convolution reverb and save the result
    """
    try:
        # Load the audio file and impulse response
        dry_signal = load_audiofile(input_path)
        dry_signal = np.array(dry_signal.get_array_of_samples(), dtype=np.float32)
        dry_signal = dry_signal / (2**15)
        impulse_response = load_audiofile(ir_path)
        impulse_response = np.array(impulse_response.get_array_of_samples(), dtype=np.float32)
        impulse_response = impulse_response / (2**15)

        # Apply reverb
        wet_signal = apply_reverb(dry_signal, impulse_response)
        
        # Mix dry and wet signals
        output_signal = mix_dry_wet(dry_signal, wet_signal, mix_ratio)
        
        # Ensure the output is normalized
        output_signal = normalize_audio(output_signal)
        
        # Save the result
        save_wave(output_path, output_signal, 16000)
        
        return True
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return False



# Example usage
if __name__ == "__main__":
    # Example paths - replace with your actual file paths
    input_file = sys.argv[1]
    impulse_response_file = sys.argv[2]
    output_file = sys.argv[3]
    
    success = process_audio_with_reverb(
        input_file,
        impulse_response_file,
        output_file,
        mix_ratio=0.4
    )
    
    if success:
        print("Reverb processing completed successfully!")
    else:
        print("Failed to process audio.")