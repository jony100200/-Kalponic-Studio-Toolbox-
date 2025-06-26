import cv2
import numpy as np
import os

def to_height(gray):
    # Normalize as float, optional contrast/curve here
    return cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

def to_normal(gray, strength=1.0):
    # Create a normal map from grayscale (basic Sobel method)
    dx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=5)
    dy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=5)
    dz = np.ones_like(gray, dtype=np.float32) * (255.0 / strength)
    normals = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.float32)
    normals[..., 0] = dx
    normals[..., 1] = dy
    normals[..., 2] = dz
    # Normalize to 0-1
    norm = np.sqrt(np.sum(normals ** 2, axis=2, keepdims=True))
    normals /= norm
    normals = normals * 0.5 + 0.5  # Map to 0..1
    normals = (normals * 255).astype(np.uint8)
    return normals[..., ::-1]  # BGR to RGB

def to_roughness(gray, invert=True):
    # Invert for stylized: dark=rough, bright=smooth
    if invert:
        return cv2.bitwise_not(gray)
    return gray

def to_ao(gray):
    # Fake AO: brighten, blur, contrast
    ao = cv2.equalizeHist(gray)
    ao = cv2.GaussianBlur(ao, (11, 11), 0)
    ao = cv2.normalize(ao, None, 128, 255, cv2.NORM_MINMAX)
    return ao

def process_image(img_path, out_folder, prefix):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Skipping {img_path} (cannot open image)")
        return
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Maps
    height = to_height(gray)
    normal = to_normal(height)
    rough = to_roughness(gray)
    ao = to_ao(gray)
    # Save maps
    cv2.imwrite(os.path.join(out_folder, f"{prefix}_Height.png"), height)
    cv2.imwrite(os.path.join(out_folder, f"{prefix}_Normal.png"), normal)
    cv2.imwrite(os.path.join(out_folder, f"{prefix}_Roughness.png"), rough)
    cv2.imwrite(os.path.join(out_folder, f"{prefix}_AmbientOcclusion.png"), ao)
    print(f"Processed: {prefix}")

def batch_process(root):
    for file in os.listdir(root):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            if '_Normal' in file or '_Height' in file or '_Roughness' in file or '_AmbientOcclusion' in file:
                continue  # Don't process already-created maps
            img_path = os.path.join(root, file)
            prefix = os.path.splitext(file)[0]
            process_image(img_path, root, prefix)
    print("Done! All maps generated.")

if __name__ == "__main__":
    base_folder = os.path.dirname(os.path.abspath(__file__))
    batch_process(base_folder)
