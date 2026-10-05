import os
import sys
from pydub import AudioSegment

if len(sys.argv) < 2:
    print("Usage: python prep_audio.py <input_audio_file> [output_file.wav]")
    sys.exit(1)

input_path = sys.argv[1]
if not os.path.exists(input_path):
    print(f"Error: File '{input_path}' not found.")
    sys.exit(1)

# Automatically name output file if not provided
if len(sys.argv) > 2:
    output_path = sys.argv[2]
else:
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = f"{base_name}_optimal_clone.wav"

print(f"Detecting format and loading: {input_path}...")

try:
    # pydub automatically detects format (.m4a, .mp3, .ogg, etc.) via extension
    audio = AudioSegment.from_file(input_path)
except Exception as e:
    print(f"Error loading audio file: {e}")
    sys.exit(1)

print("Optimizing for XTTS v2 (Converting to Mono, 24000Hz, 16-bit PCM)...")

# Force conversion to exact parameters required for best cloning performance
audio = audio.set_channels(1)                # Convert to Mono
audio = audio.set_frame_rate(24000)          # Set sample rate to 24kHz
audio = audio.set_sample_width(2)            # 16-bit PCM (2 bytes per sample)

# Export as clean uncompressed WAV
audio.export(output_path, format="wav")

print(f"Success! Optimized reference audio saved to: {output_path}")
print("You can now pass this file directly into your cloning script.")