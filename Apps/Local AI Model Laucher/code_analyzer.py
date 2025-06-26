import os
import requests
import json

LLAMA_SERVER_URL = "http://localhost:8080/completion"
TARGET_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "targets"))
ALLOWED_EXTENSIONS = [".py", ".cs", ".cpp", ".js", ".ts", ".json", ".txt", ".md"]

def is_model_running():
    print("[🔌] Checking if model is running...")
    try:
        response = requests.post(LLAMA_SERVER_URL, json={
            "prompt": "You are a helpful assistant. Reply with OK if you are running.",
            "temperature": 0.2,
            "n_predict": 20,
            "stop": ["\n"]
        })
        if response.status_code == 200:
            output = response.json().get("content", "").strip()
            print(f"[✔] Model responded: {output}")
            return True
        else:
            print("[✖] Server error:", response.status_code)
    except Exception as e:
        print(f"[✖] Cannot connect to llama-server: {e}")
    return False

def send_to_model(prompt):
    print(f"[📤] Sending prompt to model (first 500 chars):\n{prompt[:500]}\n---")
    try:
        response = requests.post(LLAMA_SERVER_URL, json={
            "prompt": prompt,
            "temperature": 0.2,
            "n_predict": 200,
            "stop": ["</s>", "###"]
        })
        if response.status_code == 200:
            content = response.json().get("content", "").strip()
            print(f"[🧠] Model returned {len(content)} characters.\n")
            return content
        else:
            print(f"[✖] Error {response.status_code} from model.")
            return "[Error] Failed to get response"
    except Exception as e:
        print(f"[✖] Exception: {e}")
        return f"[Error] Exception: {e}"

def summarize_file(file_path):
    try:
        print(f"\n[📝] Analyzing file: {file_path}")

        # Locate the prompts folder correctly
        prompt_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))

        # Find first .txt file
        prompt_file = None
        for name in os.listdir(prompt_dir):
            if name.endswith(".txt"):
                prompt_file = os.path.join(prompt_dir, name)
                break

        if not prompt_file:
            print("[❌] No prompt template found in prompts/ folder.")
            return

        # Load prompt template
        with open(prompt_file, "r", encoding="utf-8") as pfile:
            template = pfile.read()

        # Load code content
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if len(content) > 3000:
            content = content[:3000] + "\n\n[...Content Truncated...]"

        # Replace placeholders
        prompt = template.replace("{filename}", os.path.basename(file_path)).replace("{code}", content)

        print(f"[📤] Using prompt: {os.path.basename(prompt_file)}")
        summary = send_to_model(prompt)

        # Save summary
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, os.path.basename(file_path) + ".summary.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"[💾] Saved summary to: {out_path}")
        return summary
    except Exception as e:
        print(f"[✖] Error processing {file_path}: {e}")
        return f"[Error reading {file_path}]: {e}"

def analyze_codebase(target_folder):
    if not is_model_running():
        print("[!] No active model detected. Please start llama-server.")
        return

    print(f"\n[📂] Analyzing codebase in: {target_folder}")
    found = False
    for root, _, files in os.walk(target_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                found = True
                file_path = os.path.join(root, file)
                print(f"[➡] Found eligible file: {file_path}")
                summarize_file(file_path)

    if not found:
        print("[❗] No valid files found in target folder.")

# Entry point
if __name__ == "__main__":
    analyze_codebase(TARGET_FOLDER)
