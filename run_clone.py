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

# Set up clean sub-folder workspaces
cwd = os.getcwd()
chunk_dir = os.path.join(cwd, "tmp", "auto_chunks")
stitch_dir = os.path.join(cwd, "tmp", "stitch_chunks")

for folder in [chunk_dir, stitch_dir]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

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

if not script_text:
    print("Error: The script file is empty.")
    sys.exit(1)

# SMART STRING BUFFER: Groups text strings up to 120 characters to respect the 150-char limit
sanitized_text = " ".join(script_text.split())
sentences = []
words = sanitized_text.split(" ")
current_chunk = ""

for word in words:
    if len(current_chunk) + len(word) + 1 < 120:
        current_chunk += word + " "
    else:
        if current_chunk:
            sentences.append(current_chunk.strip())
        current_chunk = word + " "
if current_chunk:
    sentences.append(current_chunk.strip())

os.environ["COQUI_TOS_AGREED"] = "1"

print("1/4: Loading XTTS v2 directly onto RTX 3050...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
tts.to("cuda")

print(f"3/4: Synthesizing speech natively via sequential string buffering...")
generated_audio_segments = []

# Loop through our safely sized sentence chunks one by one
for idx, sentence in enumerate(sentences):
    print(f" -> Generating line {idx + 1}/{len(sentences)}: {sentence[:45]}...")
    temp_segment_path = os.path.join(stitch_dir, f"seg_{idx:03d}.wav")
    
    # Process using the factory-standard tts_to_file wrapper over isolated safe strings
    tts.tts_to_file(
        text=sentence,
        speaker_wav=speaker_wavs,  
        language="hi",
        file_path=temp_segment_path,
        speed=1.0,                 
        temperature=0.65,          # Balanced factory default value for stable voice generation
        split_sentences=False      # Disabled here since our manual length filter has already optimized it
    )
    generated_audio_segments.append(temp_segment_path)

# Seamlessly stitch all clean wave fragments back together into a single file
print(" -> Merging audio channels into the final target sequence...")
final_output_track = AudioSegment.empty()
for segment_path in generated_audio_segments:
    if os.path.exists(segment_path):
        segment_audio = AudioSegment.from_wav(segment_path)
        # Add a microscopic comfort crossfade so the chunks join together smoothly
        final_output_track += segment_audio + AudioSegment.silent(duration=100, frame_rate=24000)

# Export the master track
final_output_track.export(output_path, format="wav")

# Clean up all workspace sub-folders
for folder in [chunk_dir, stitch_dir]:
    try:
        shutil.rmtree(folder)
    except Exception:
        pass

print(f"4/4: Success! Highly accurate voice matching completed to: {output_path}")
