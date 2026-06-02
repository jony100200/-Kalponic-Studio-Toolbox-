from pathlib import Path
import re

from PIL import Image
import imagehash
import cv2
from rapidfuzz import fuzz
from skimage.metrics import structural_similarity as ssim


IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"
}


def clean_name(file_name: str) -> str:
    name = Path(file_name).stem.lower()

    remove_words = [
        "cleaned", "final", "done", "upscaled", "edited",
        "copy", "new", "fixed", "output", "result",
        "v1", "v2", "v3", "v4"
    ]

    for word in remove_words:
        name = name.replace(word, "")

    name = re.sub(r"[^a-z0-9]+", " ", name)
    return name.strip()


def get_images(folder: Path) -> list[Path]:
    return [
        file for file in folder.rglob("*")
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    ]


def load_image_cv(path: Path, size=(512, 512)):
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if img is None:
        return None

    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)


def phash_score(path_a: Path, path_b: Path) -> float:
    try:
        with Image.open(path_a) as img_a, Image.open(path_b) as img_b:
            hash_a = imagehash.phash(img_a.convert("RGB"))
            hash_b = imagehash.phash(img_b.convert("RGB"))

        distance = hash_a - hash_b
        return max(0, min(100 - distance * 3, 100))

    except Exception:
        return 0


def ssim_score(path_a: Path, path_b: Path) -> float:
    img_a = load_image_cv(path_a)
    img_b = load_image_cv(path_b)

    if img_a is None or img_b is None:
        return 0

    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)

    return max(0, min(ssim(gray_a, gray_b) * 100, 100))


def color_hist_score(path_a: Path, path_b: Path) -> float:
    img_a = load_image_cv(path_a)
    img_b = load_image_cv(path_b)

    if img_a is None or img_b is None:
        return 0

    hsv_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2HSV)
    hsv_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2HSV)

    hist_a = cv2.calcHist([hsv_a], [0, 1], None, [50, 60], [0, 180, 0, 256])
    hist_b = cv2.calcHist([hsv_b], [0, 1], None, [50, 60], [0, 180, 0, 256])

    cv2.normalize(hist_a, hist_a)
    cv2.normalize(hist_b, hist_b)

    similarity = cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)
    return max(0, min(similarity * 100, 100))


def final_score(name_score, phash, structure, color):
    return (
        name_score * 0.25 +
        phash * 0.35 +
        structure * 0.25 +
        color * 0.15
    )


def compare_folders(
    source_folder: str,
    target_folder: str,
    done_threshold: float = 75,
    maybe_threshold: float = 50,
    log_callback=None,
):
    source = Path(source_folder).resolve()
    target = Path(target_folder).resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")

    if not target.exists():
        raise FileNotFoundError(f"Target folder does not exist: {target}")

    def log(text):
        if log_callback:
            log_callback(text)
        else:
            print(text)

    source_images = get_images(source)
    target_images = get_images(target)

    log(f"Source images: {len(source_images)}")
    log(f"Target images: {len(target_images)}")
    log("")

    report = []
    done = []
    maybe = []
    not_done = []

    target_clean_names = [(img, clean_name(img.name)) for img in target_images]

    for index, source_img in enumerate(source_images):
        clean_source = clean_name(source_img.name)
        best = None

        for target_img, clean_target in target_clean_names:
            name_score = fuzz.ratio(clean_source, clean_target)

            if name_score < 30:
                continue

            p_score = phash_score(source_img, target_img)
            s_score = ssim_score(source_img, target_img)
            c_score = color_hist_score(source_img, target_img)

            score = final_score(name_score, p_score, s_score, c_score)

            if best is None or score > best["score"]:
                best = {
                    "target": target_img,
                    "score": score,
                    "name": name_score,
                    "phash": p_score,
                    "ssim": s_score,
                    "color": c_score,
                }

        if best is None:
            not_done.append(source_img)
            line = f"NOT DONE | {source_img.name}"
        else:
            if best["score"] >= done_threshold:
                done.append(source_img)
                status = "DONE"
            elif best["score"] >= maybe_threshold:
                maybe.append(source_img)
                status = "MAYBE"
            else:
                not_done.append(source_img)
                status = "NOT DONE"

            line = (
                f"{status} | Score {best['score']:.1f} | "
                f"Name {best['name']:.1f} | pHash {best['phash']:.1f} | "
                f"SSIM {best['ssim']:.1f} | Color {best['color']:.1f} | "
                f"{source_img.name} -> {best['target'].name}"
            )

        report.append(line)
        log(f"[{index + 1}/{len(source_images)}] {line}")

    report.append("")
    report.append("========== SUMMARY ==========")
    report.append(f"Done     : {len(done)}")
    report.append(f"Maybe    : {len(maybe)}")
    report.append(f"Not Done : {len(not_done)}")
    report.append(f"Total    : {len(source_images)}")

    report_path = source / "image_compare_report.txt"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("\n".join(report))

    return {
        "done": len(done),
        "maybe": len(maybe),
        "not_done": len(not_done),
        "total": len(source_images),
        "report_path": str(report_path),
    }