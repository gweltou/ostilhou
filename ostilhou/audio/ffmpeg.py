import subprocess



def stream_audio_file(
    input_file: str,
    sample_rate: int,
    callback: callable,
    buffer_size = 8000,
):
    # Configure ffmpeg to output raw audio in the format we need
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', input_file,
        '-ar', str(sample_rate),  # 16kHz sample rate
        '-ac', '1',      # Mono
        '-f', 's16le',   # 16-bit signed little-endian PCM
        '-',             # Output to stdout
        '-loglevel', 'error'  # Reduce ffmpeg output
    ]

    with subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE
    ) as process:
        while True:
            data = process.stdout.read(buffer_size)
            if len(data) == 0:
                break
            callback(data)
