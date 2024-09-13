import sounddevice as sd
import numpy as np
import whisper
from queue import Queue
from threading import Thread, Event
import keyboard
import time
from scipy.signal import resample

MODEL_SIZE = "small"  #tiny, small, base,...
model = whisper.load_model(MODEL_SIZE)

# Audio settings
SAMPLE_RATE = 16000  # Whisper expects 16kHz audio
CHANNELS = 1
DTYPE = np.float32
MIC_RATE = 48000  # normal microphone sample rate

audio_queue = Queue()
is_recording = Event()
transcription_queue = Queue()

#resample audio from 48kHz to 16kHz
def resample_audio(audio_chunk, original_rate, target_rate):
    num_samples = int(len(audio_chunk) * target_rate / original_rate)
    return resample(audio_chunk, num_samples)

#audio input
def audio_callback(indata, frames, time, status):
    if is_recording.is_set():
        audio_chunk = indata.flatten().astype(DTYPE)
        resampled_chunk = resample_audio(audio_chunk, MIC_RATE, SAMPLE_RATE)  # Resample to 16kHz
        audio_queue.put(resampled_chunk)

#transcribe
def transcribe_audio():
    buffer = np.array([], dtype=DTYPE)
    while True:
        if not is_recording.is_set() and audio_queue.empty():
            time.sleep(0.05)
            continue

        while not audio_queue.empty():
            chunk = audio_queue.get()
            buffer = np.append(buffer, chunk)

        if len(buffer) >= SAMPLE_RATE * 1:  # Process 1 second of audio
            audio = whisper.pad_or_trim(buffer)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            options = whisper.DecodingOptions(fp16=False, language='vi', without_timestamps=True)
            result = whisper.decode(model, mel, options)

            if result.text.strip():
                transcription_queue.put(result.text)

            #Clear the buffer
            buffer = np.array([], dtype=DTYPE)

# Start the audio stream
stream = sd.InputStream(
    samplerate=MIC_RATE,
    channels=CHANNELS,
    dtype=DTYPE,
    callback=audio_callback
)

# Start the transcription thread
transcription_thread = Thread(target=transcribe_audio, daemon=True)
transcription_thread.start()

# Main loop
print(f"Using Whisper model: {MODEL_SIZE}")
print("Nhấn và giữ SPACE để ghi âm, thả ra để dừng. Nhấn ESC để thoát.")
full_transcript = ""
with stream:
    while True:
        if keyboard.is_pressed('space'):
            if not is_recording.is_set():
                is_recording.set()
                print("\nĐang ghi âm...", end='', flush=True)
        else:
            if is_recording.is_set():
                is_recording.clear()
                print("\nĐã dừng ghi âm.")
                # Clear remaining audio
                while not audio_queue.empty():
                    audio_queue.get()

                # Clear buffer after recording
                buffer = np.array([], dtype=DTYPE)

        # Process transcription
        while not transcription_queue.empty():
            transcription = transcription_queue.get()
            print(transcription, end=' ', flush=True)
            full_transcript += transcription + " "

        if keyboard.is_pressed('esc'):
            print("\nĐang thoát...")
            break

        time.sleep(0.05)  #Delay to prevent CPU usage

#Save transcript to a file
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(full_transcript)

print("\nPhiên âm đã được lưu vào output.txt")
