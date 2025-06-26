import os
import time
from datetime import datetime
from faster_whisper import WhisperModel

# ====== SETTINGS ======
MODEL_SIZE = "large-v2"
AUDIO_EXTENSIONS = {
    '.wav', '.mp3', '.m4a', '.mp4', '.flac', '.aac', '.ogg', '.mkv', '.mov', '.avi'
}
OUTPUT_ROOT = "GeneratedTranscripts"

# ====== UTILS ======
def is_audio_file(filename):
    return os.path.splitext(filename)[1].lower() in AUDIO_EXTENSIONS

def write_transcript(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as out:
        for segment in segments:
            out.write(segment.text.strip() + "\n")

def transcribe_file(model, filepath, outfolder):
    try:
        start_time = time.time()
        segments, _ = model.transcribe(filepath)
        base = os.path.splitext(os.path.basename(filepath))[0]
        transcript_path = os.path.join(outfolder, base + ".txt")
        write_transcript(segments, transcript_path)
        elapsed = time.time() - start_time
        print(f"✅ {base} done in {elapsed:.1f}s → {transcript_path}")
        return True
    except Exception as e:
        print(f"❌ Failed {filepath}: {e}")
        return False

# ====== MAIN ======
if __name__ == "__main__":
    print("\n🎧 SubGen Batch Transcriber")
    print("──────────────────────────────────────────────")

    # Create time-stamped output folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = os.path.join(OUTPUT_ROOT, f"Run_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)

    files = [f for f in os.listdir() if is_audio_file(f)]
    total_files = len(files)

    if not files:
        print("⚠️ No audio/video files found in this folder.")
        exit()

    print(f"📂 Found {total_files} file(s) to process: {[os.path.basename(f) for f in files]}\n")

    model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")

    success, failed = 0, 0
    batch_start = time.time()

    for idx, f in enumerate(files, 1):
        print(f"\n[{idx}/{total_files}] Transcribing: {f}")
        if transcribe_file(model, f, output_folder):
            success += 1
        else:
            failed += 1

    total_time = time.time() - batch_start
    print("\n📊 Summary")
    print("──────────────────────────────────────────────")
    print(f"✅ {success} succeeded")
    print(f"❌ {failed} failed")
    print(f"⏱️ Time taken: {total_time:.1f} seconds")
    print(f"📁 Output saved to: {output_folder}\n")
