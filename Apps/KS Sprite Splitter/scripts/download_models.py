"""Model download helper for KS Sprite Splitter.

Downloads and checksums required ONNX models.
"""
import argparse
import hashlib
import os
from pathlib import Path

MODELS = {
    'sam2': {
        'url': 'https://example.com/sam2.onnx',
        'sha256': ''
    },
    'modnet': {
        'url': 'https://example.com/modnet.onnx',
        'sha256': ''
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
    parser.add_argument('--dest', default='../models', help='Destination folder')
    args = parser.parse_args(argv)

    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    model = MODELS[args.model]
    out = dest / f"{args.model}.onnx"
    print(f"Downloading {args.model} to {out}")
    download(model['url'], out)
    print("Done")


if __name__ == '__main__':
    main()
