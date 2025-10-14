# KS Sprite Splitter

Auto-separate 2D sprites into semantic parts with soft mattes and channel-packed maps.

Quickstart
---------

1. Install dependencies (recommended in a virtualenv):

```powershell
python -m pip install -r requirements.txt
```

2. Run the CLI (stub):

```powershell
python -m cli.ks_splitter --in samples/ --out runs/ --category auto
```

3. Download models (edit `scripts/download_models.py` URLs first):

```powershell
python scripts/download_models.py --model sam2 --dest models/
```

License: MIT
