import sys
import os
import json
import subprocess
import platform

"""Pathline Model Server Launcher

This script reads a JSON configuration (config.json by default) and
starts a model server. It supports launching either a file-based model
(e.g. GGUF Llama) or a folder-based model such as Faster-Whisper.
The launcher can optionally activate a virtual environment and inject
CUDA paths before spawning the server process.
"""


def print_header() -> None:
    """Print CLI header."""
    print("\n🧠 Pathline | Model Server Launcher")
    print("──────────────────────────────────────────────")


def print_usage() -> None:
    """Display basic usage instructions."""
    print_header()
    print("📘 Usage:")
    print("  python run_model_server.py [file|folder] <model_path> [server] [port]")
    print("  python run_model_server.py --config path/to/config.json")
    print("  If no arguments are given, 'config.json' in this directory is used.\n")
    if os.name == "nt":
        input("Press Enter to exit...")


def load_config(path: str = "config.json") -> dict | None:
    """Load JSON config if it exists."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                print(f"⚙️  Loaded config: {path}")
                return json.load(f)
        except Exception as exc:  # pragma: no cover - simple CLI
            print(f"❌ Failed to load {path}: {exc}")
    return None


def inject_cuda_paths(env: dict, paths: list[str]) -> None:
    """Prepend CUDA binary paths to PATH."""
    for p in paths:
        if os.path.isdir(p):
            env["PATH"] = f"{p}{os.pathsep}" + env.get("PATH", "")
            print(f"🔧 Added CUDA path: {p}")


def activate_virtualenv(env: dict, venv: str) -> None:
    """Activate a Python virtual environment by tweaking env vars."""
    if not os.path.isdir(venv):
        print(f"⚠️  Virtual env not found: {venv}")
        return
    env["VIRTUAL_ENV"] = venv
    if platform.system() == "Windows":
        bin_path = os.path.join(venv, "Scripts")
    else:
        bin_path = os.path.join(venv, "bin")
    env["PATH"] = f"{bin_path}{os.pathsep}" + env.get("PATH", "")
    print(f"📦 Activated virtual environment: {venv}")


def launch_cmd(cmd: list[str], env: dict) -> None:
    """Launch command in a new terminal window if possible."""
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["cmd", "/k"] + cmd, env=env)
    else:
        subprocess.Popen(["bash", "-c", " ".join(cmd)], env=env)
    print("✅ Server launched. Close the new terminal to stop it.")


def main() -> None:
    print_header()

    # Parse arguments
    args = sys.argv[1:]
    cfg = None
    if not args:
        cfg = load_config()
    elif args[0] == "--config" and len(args) >= 2:
        cfg = load_config(args[1])
    elif len(args) >= 2:
        cfg = {
            "model_type": args[0],
            "model_path": args[1],
        }
        if len(args) >= 3:
            cfg["server"] = args[2]
        if len(args) >= 4:
            cfg["port"] = args[3]
    else:
        print_usage()
        return

    if not cfg:
        print_usage()
        return

    model_type = cfg.get("model_type")
    model_path = cfg.get("model_path")
    server = cfg.get("server") or cfg.get("server_exe") or cfg.get("server_script")
    port = str(cfg.get("port", "8181"))
    cuda_paths = cfg.get("cuda_paths", [])
    venv_path = cfg.get("venv_activate")

    if not model_type or not model_path:
        print("❌ Config missing 'model_type' or 'model_path'.")
        return
    if not os.path.exists(model_path):
        print(f"❌ Model path does not exist → {model_path}")
        return

    env = os.environ.copy()
    if venv_path:
        activate_virtualenv(env, venv_path)
    inject_cuda_paths(env, cuda_paths)

    cmd: list[str] = []
    if model_type == "file":
        if not model_path.lower().endswith(".gguf"):
            print("❌ Model path must be a .gguf file for 'file' type.")
            return
        exe = server or "llama-server.exe"
        print(f"🧠 Launching LLM: {os.path.basename(exe)}")
        cmd = [exe, "--model", model_path, "--port", port]
    elif model_type == "folder":
        if server and "llama" in os.path.basename(server).lower():
            print("❌ Refusing to launch llama server for folder type.")
            return
        if server and server.endswith(".py"):
            print(f"🔊 Launching Python server: {os.path.basename(server)}")
            cmd = ["python", server, model_path, port]
        else:
            exe = server or "whisper-server.exe"
            print(f"🎤 Launching whisper server: {os.path.basename(exe)}")
            cmd = [exe, "--model_dir", model_path, "--port", port]
    else:
        print("❌ Invalid model_type. Must be 'file' or 'folder'.")
        return

    print("📤 Command:", " ".join(cmd))
    launch_cmd(cmd, env)


if __name__ == "__main__":
    main()

# End of file
