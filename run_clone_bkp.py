import os
import sys
import shutil
from pydub import AudioSegment
from TTS.api import TTS

# Validate command-line arguments
if len(sys.argv) < 4:
    print("Error: Missing arguments!")
    sys.exit(1)

audio_arg = sys.argv[1]
script_path = sys.argv[2]
output_path = sys.argv[3]

if not os.path.exists(script_path):
    print("Error: Script path not found.")
    sys.exit(1)

# Set up clean sub-folder workspace
cwd = os.getcwd()
chunk_dir = os.path.join(cwd, "tmp", "auto_chunks")
if os.path.exists(chunk_dir):
    shutil.rmtree(chunk_dir)
os.makedirs(chunk_dir, exist_ok=True)

# Parse multiple recording files passed from PowerShell string pipeline
if "|" in audio_arg:
    input_recordings = [p.strip() for p in audio_arg.split("|") if p.strip()]
else:
    input_recordings = [audio_arg.strip()]

speaker_wavs = []
global_chunk_count = 0

print(f" -> Found {len(input_recordings)} total audio input recordings to process...")

# Dynamic Multi-Slicing Loop: Auto-extracts 10 equal parts out of EACH unique input track
for file_idx, recording_file in enumerate(input_recordings):
    if not os.path.exists(recording_file):
        continue
    
    print(f"   -> Slicing Track {file_idx + 1}: {os.path.basename(recording_file)}")
    try:
        full_audio = AudioSegment.from_file(recording_file)
        total_ms = len(full_audio)
        chunk_length_ms = total_ms // 10
        
        for i in range(10):
            start_time = i * chunk_length_ms
            end_time = (i + 1) * chunk_length_ms if i < 9 else total_ms
            
            chunk = full_audio[start_time:end_time]
            chunk_file_path = os.path.join(chunk_dir, f"track_{file_idx:02d}_chunk_{i:02d}.wav")
            
            chunk.export(chunk_file_path, format="wav")
            speaker_wavs.append(chunk_file_path)
            global_chunk_count += 1
            
    except Exception as e:
        print(f"Error processing slices for track {recording_file}: {e}")
        sys.exit(1)

print(f" -> Auto-chunking complete! Collected {global_chunk_count} safe voice vectors for voice fingerprinting.")

# Read the script text
with open(script_path, "r", encoding="utf-8") as f:
    script_text = f.read().strip()

os.environ["COQUI_TOS_AGREED"] = "1"

print("1/4: Loading XTTS v2 directly onto RTX 3050...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
tts.to("cuda")

print(f"3/4: Synthesizing speech using massive multi-sample voice vector averaging...")
tts.tts_to_file(
    text=script_text,
    speaker_wav=speaker_wavs,  # Feeds all 10*N auto-extracted slice variants natively
    language="hi",
    file_path=output_path,
    speed=1.0,                 # Smooth, factory standard pacing
    temperature=0.1,
    split_sentences=True
)

# Workspace cleanup
try:
    shutil.rmtree(chunk_dir)
except Exception:
    pass

print(f"4/4: Success! Highly accurate voice matching completed to: {output_path}")
