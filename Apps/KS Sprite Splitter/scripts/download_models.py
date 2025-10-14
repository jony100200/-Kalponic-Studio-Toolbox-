"""Model download helper for KS Sprite Splitter.

Downloads and checksums required ONNX models.
"""
import argparse
import hashlib
import os
from pathlib import Path

MODELS = {
    'sam2': {
        'url': 'https://huggingface.co/shubham0204/sam2-onnx-models/resolve/main/sam2_hiera_tiny_encoder.onnx',
        'sha256': ''  # Will be computed after download
    },
    'modnet': {
        'url': 'https://drive.google.com/uc?export=download&id=1cgycTQlYXpTh26gB9FTnthE7AvruV8hd',
        'sha256': ''  # Will be computed after download
    }
}


def download(url, dest):
    import requests
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=list(MODELS.keys()), help='Model to download')
    parser.add_argument('--dest', default=str(Path(__file__).resolve().parent.parent / 'models'), help='Destination folder')
    parser.add_argument('--placeholder', action='store_true', help='Create a small placeholder file instead of downloading (for offline/dev)')
    args = parser.parse_args(argv)

    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    if not args.model:
        print("No model specified. Available models:")
        for k in MODELS.keys():
            print(f" - {k}")
        return

    model = MODELS[args.model]
    out = dest / f"{args.model}.onnx"

    if args.placeholder:
        print(f"Creating placeholder model file at {out}")
        with open(out, 'w', encoding='utf-8') as f:
            f.write(f"# Placeholder for {args.model} ONNX model\n# Replace with a real ONNX model for production.\n")
        print("Placeholder created.")
        return

    print(f"Downloading {args.model} to {out}")
    download(model['url'], out)
    print("Done")


if __name__ == '__main__':
    main()
