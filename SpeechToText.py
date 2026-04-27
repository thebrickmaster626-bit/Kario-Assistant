import pyaudio
import numpy as np
from faster_whisper import WhisperModel

# --- Setup ---
device = "cpu"
model = WhisperModel("small", device=device, compute_type="float32")
print_vol = True


def record_until_silence(
    silence_threshold=600,
    silence_chunks=20,
    chunk_size=2048,
    rate=16000,
    channels=1
):
    """
    Records audio from the microphone until silence is detected.
    Returns audio as float32 at 16kHz for direct Whisper transcription.
    """

    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=chunk_size
    )

    frames = []
    silent_counter = 0
    speaking = False
    warmup_chunks = 3
    chunk_index = 0

    print("Recording... Speak now!")

    try:
        while True:
            data = stream.read(chunk_size, exception_on_overflow=False)
            chunk_index += 1

            if chunk_index < warmup_chunks:
                continue

            frames.append(data)

            # Convert chunk to numpy for volume detection
            audio_data = np.frombuffer(data, dtype=np.int16)

            if audio_data.size == 0:
                continue

            volume = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))

            if not np.isfinite(volume):
                continue

            if  print_vol:
                print(volume)

            if volume > silence_threshold:
                speaking = True
                silent_counter = 0
            else:
                if speaking:
                    silent_counter += 1
                    if silent_counter > silence_chunks:
                        print("Silence detected, stopping recording.")
                        break

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_int16 = np.frombuffer(b"".join(frames), dtype=np.int16)

        if audio_int16.size == 0:
            print("No audio captured.")
            return None

        # convert safely to float32 [-1, 1]
        raw_audio = audio_int16.astype(np.float32) / 32768.0

        raw_audio = np.nan_to_num(raw_audio, nan=0.0, posinf=0.0, neginf=0.0)
        raw_audio = np.clip(raw_audio, -1.0, 1.0).astype(np.float32)
        return raw_audio

def record_and_transcribe():
    """
    Records audio and returns Whisper transcription.
    """

    audio_data = record_until_silence()
    if audio_data is None or audio_data.size == 0:
        return ""

    print("audio stats:",
          "len", audio_data.size,
          "min", float(np.min(audio_data)),
          "max", float(np.max(audio_data)),
          "finite", bool(np.isfinite(audio_data).all()))

    print("Transcribing...")

    segments, info = model.transcribe(
        audio_data,
        language="en",
        beam_size=1,
        best_of=1,
        condition_on_previous_text=False,
        vad_filter=False,
    )

    text = "".join([seg.text for seg in segments])

    print("--- Transcription ---")
    print(text)

    return text
