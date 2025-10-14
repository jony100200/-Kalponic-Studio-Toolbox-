"""Export per-part color, grayscale matte and binary masks for KS Sprite Splitter

Produces for each part:
 - color_<part>.png   (RGBA, original color multiplied by soft alpha)
 - matte_gray_<part>.png (grayscale soft matte 0..255)
 - mask_<part>.png     (binary mask 0 or 255)

Looks for either soft mattes in the run folder named `matte_<part>.png` or a
channel-packed `parts.tga` (R/G/B channels map to parts in order). If neither
is found the script raises an error and suggests running the pipeline first.

Usage:
  python scripts/export_color_parts.py --image samples/test_sprite.png --out runs/Run_xxx --parts Leaves Trunk

"""
from pathlib import Path
import argparse
import cv2
import numpy as np


def read_image_rgba(path: Path):
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Cannot read image {path}")
    # Ensure 4 channels (RGBA) in float32 0..1 order RGBA
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 3:
        b,g,r = cv2.split(img)
        a = np.full_like(b, 255)
        img = cv2.merge([r,g,b,a])
    else:
        b,g,r,a = cv2.split(img)
        img = cv2.merge([r,g,b,a])
    img = img.astype(np.float32) / 255.0
    return img


def read_matte(path: Path):
    m = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if m is None:
        return None
    if m.ndim == 3:
        # matte might be RGB - convert to gray
        gray = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    else:
        gray = m
    return gray.astype(np.float32) / 255.0


def read_parts_tga(path: Path):
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    # OpenCV reads BGR(A). We want channels in RGB order
    if img.shape[2] >= 3:
        b,g,r = cv2.split(img[:,:,:3])
        channels = [r.astype(np.float32)/255.0, g.astype(np.float32)/255.0, b.astype(np.float32)/255.0]
        return channels
    return None


def write_rgba_png(path: Path, rgba: np.ndarray):
    # rgba float32 0..1 -> BGRA uint8 for cv2
    rgb = (rgba[..., :3] * 255.0).astype(np.uint8)
    bgr = rgb[..., ::-1]
    alpha = (rgba[..., 3] * 255.0).astype(np.uint8)
    bgra = cv2.merge([bgr[:,:,0], bgr[:,:,1], bgr[:,:,2], alpha])
    cv2.imwrite(str(path), bgra)


def write_gray(path: Path, gray: np.ndarray):
    # gray float32 0..1
    out = (np.clip(gray, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), out)


def write_binary_mask(path: Path, mask: np.ndarray, thresh: float = 0.5):
    binm = (mask >= thresh).astype(np.uint8) * 255
    cv2.imwrite(str(path), binm)


def export_part(orig_rgba: np.ndarray, mask: np.ndarray, out_prefix: Path, part_name: str):
    # mask: float32 0..1
    h_img, w_img = orig_rgba.shape[:2]
    if mask.shape[:2] != (h_img, w_img):
        mask = cv2.resize(mask, (w_img, h_img), interpolation=cv2.INTER_LINEAR)

    # color: multiply original RGB by mask; alpha = mask
    color_rgba = np.zeros((h_img, w_img, 4), dtype=np.float32)
    color_rgba[..., :3] = orig_rgba[..., :3] * mask[..., np.newaxis]
    color_rgba[..., 3] = mask

    # write files
    out_color = out_prefix / f"color_{part_name}.png"
    out_gray = out_prefix / f"matte_gray_{part_name}.png"
    out_mask = out_prefix / f"mask_{part_name}.png"

    write_rgba_png(out_color, color_rgba)
    write_gray(out_gray, mask)
    write_binary_mask(out_mask, mask)
    print(f"Exported part '{part_name}':\n  {out_color}\n  {out_gray}\n  {out_mask}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Original color image (input)")
    parser.add_argument("--out", required=True, help="Run output folder where KS mattes or parts.tga live (will also receive outputs)")
    parser.add_argument("--parts", nargs='+', required=True, help="Part names in order (e.g. Leaves Trunk)")
    parser.add_argument("--parts-tga", default='parts.tga', help="Channel-packed parts file name (default: parts.tga)")
    args = parser.parse_args()

    image_path = Path(args.image)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    orig = read_image_rgba(image_path)

    # try soft mattes first
    mattes_found = False
    for part in args.parts:
        matte_path = out_dir / f"matte_{part}.png"
        if matte_path.exists():
            mattes_found = True
            mask = read_matte(matte_path)
            export_part(orig, mask, out_dir, part)

    if mattes_found:
        return

    # fallback to channel-packed parts.tga
    tga_path = out_dir / args.parts_tga
    channels = read_parts_tga(tga_path)
    if channels:
        for idx, part in enumerate(args.parts):
            if idx >= len(channels):
                print(f"No channel for part index {idx} -> {part}")
                break
            mask = channels[idx]
            export_part(orig, mask, out_dir, part)
        return

    raise FileNotFoundError("No per-part mattes found and no parts.tga present. Run KS pipeline first or provide mattes in the run folder.")


if __name__ == '__main__':
    main()
