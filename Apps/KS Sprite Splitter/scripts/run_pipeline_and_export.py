"""Run KS pipeline on the sample sprite and export per-part color/matte/mask

This helper runs the `PipelineRunner` on `samples/test_sprite.png` using the
`tree` template, then discovers produced mattes and calls
`scripts/export_color_parts.py` to write color/matte/mask files.

Usage:
  python scripts/run_pipeline_and_export.py
"""
from pathlib import Path
import subprocess
import sys
import yaml

def main():
    root = Path(__file__).resolve().parent.parent
    sample = root / 'samples' / 'test_sprite.png'
    if not sample.exists():
        print('Sample image not found:', sample)
        sys.exit(1)

    # Load config and run pipeline
    cfg_path = root / 'configs' / 'config.yml'
    cfg = yaml.safe_load(cfg_path.read_text())

    # Import here to keep script fast when not used
    # Make project root importable (so `ks_splitter` package can be found)
    import sys
    proj_root = root
    if str(proj_root) not in sys.path:
        sys.path.insert(0, str(proj_root))
    from ks_splitter.pipeline import PipelineRunner

    runner = PipelineRunner(cfg)
    print('Running pipeline on', sample)
    run_dir = runner.run(str(sample), str(root / 'runs'), category='tree')
    print('Pipeline finished. Run dir:', run_dir)

    # Find separated image dir
    img_name = sample.stem
    separated_dir = Path(run_dir) / 'Separated' / img_name
    if not separated_dir.exists():
        print('Expected separated dir not found:', separated_dir)
        sys.exit(1)

    # Discover matte files
    mattes = sorted(separated_dir.glob('matte_*.png'))
    if mattes:
        parts = [p.stem[len('matte_'):] for p in mattes]
        print('Found parts from mattes:', parts)
    else:
        # Fallback: check packed parts image
        if (separated_dir / 'parts.png').exists() or (separated_dir / 'parts.tga').exists():
            # Use a reasonable default mapping if user didn't supply template names
            parts = ['Part0','Part1','Part2']
            print('No matte_*.png found; will attempt export using channel-packed parts with default names:', parts)
        else:
            print('No mattes or packed parts found in', separated_dir)
            sys.exit(1)

    # Call exporter script
    exporter = root / 'scripts' / 'export_color_parts.py'
    cmd = [sys.executable, str(exporter), '--image', str(sample), '--out', str(separated_dir), '--parts'] + parts
    print('Calling exporter:', ' '.join(cmd))
    subprocess.check_call(cmd)
    print('Export complete. Outputs in', separated_dir)


if __name__ == '__main__':
    main()
