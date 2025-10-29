import numpy as np
from PIL import Image

def apply_mask_make_transparent(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Restituisce una copia RGBA di `img` (tipo int32) in cui
    i pixel per i quali la `mask` NON è considerata opaca
    vengono resi trasparenti (alpha=0) e RGB messi a 0.
    Accetta mask in formato grayscale, RGB o RGBA.
    """
    h, w = img.shape[:2]
    img_rgba = to_rgba(img, h, w)  # usa la funzione presente nel file

    m = np.array(mask)
    # costruisci mask_keep: True = mantenere, False = rendere trasparente
    if m.ndim == 3 and m.shape[2] == 4:
        rgb = m[:, :, :3]
        alpha = m[:, :, 3]
        white_mask = np.all(rgb == 255, axis=2)
        alpha_mask = (alpha == 255)
        mask_keep = white_mask | alpha_mask
    elif m.ndim == 3 and m.shape[2] == 3:
        mask_keep = np.all(m == 255, axis=2)
    else:
        mask_keep = (m != 0)

    if mask_keep.shape != (h, w):
        mask_img = Image.fromarray((mask_keep.astype('uint8') * 255))
        mask_img = mask_img.resize((w, h), resample=Image.NEAREST)
        mask_keep = (np.array(mask_img) > 0)

    mask_keep = mask_keep.astype(bool)

    # rendi trasparenti i pixel NON keep
    inv = ~mask_keep
    if inv.any():
        img_rgba[inv, :3] = 0
        img_rgba[inv, 3] = 0

    return img_rgba

def to_rgba(arr: np.ndarray, h, w) -> np.ndarray:
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=2)
    if arr.shape[2] == 4:
        return arr.astype(np.int32)
    if arr.shape[2] == 3:
        alpha = np.full((h, w, 1), 255, dtype=arr.dtype)
        return np.concatenate([arr, alpha], axis=2).astype(np.int32)
    raise ValueError("Unsupported channel count")


# P.S. Figo numpy ma abbastanza fastidioso da scrivere, java no vero?
def compare_images_alpha_overlap(
        img0: np.ndarray,
        img1: np.ndarray
) -> tuple[float, int]:
    """
    Confronta due immagini (array NumPy) della stessa dimensione.
    Considera solo i pixel dove entrambi hanno alpha > 0.
    Se gli array sono RGB vengono promossi a RGBA con alpha=255.
    `extra_mask` (bool) viene applicata in AND col criterio di alpha-overlap.
    Restituisce (score_mean, n_pixels). Se non ci sono pixel confrontabili
    ritorna (inf, 0).
    """
    if img0.shape[:2] != img1.shape[:2]:
        raise ValueError("Le immagini devono avere la stessa dimensione")

    h, w = img0.shape[:2]
    ra = to_rgba(img0, h, w)
    rb = to_rgba(img1, h, w)

    # maks out transparent pixels
    alpha_overlap = (ra[:, :, 3] > 0) & (rb[:, :, 3] > 0)

    n = int(np.count_nonzero(alpha_overlap))
    if n == 0:
        return float("inf"), 0

    diff = np.abs(ra[:, :, :3].astype(np.float64) - rb[:, :, :3].astype(np.float64)).mean(axis=2)
    vals = diff[alpha_overlap]
    return float(vals.mean()), n


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt
    os.chdir("../resources")
    mask = np.array(Image.open("ignoreZone_alpha.png"))

    a = np.array(Image.open("screenshot_0.png"))
    b = np.array(Image.open("screenshot_0.png"))
    print(compare_images_alpha_overlap(a, b))

    a = np.array(Image.open("screenshot_1.png"))
    b = np.array(Image.open("screenshot_1.png"))
    a = apply_mask_make_transparent(a, mask)
    b = apply_mask_make_transparent(b, mask)
    print(compare_images_alpha_overlap(a, b))

    a = np.array(Image.open("screenshot_0.png"))
    b = np.array(Image.open("screenshot_1.png"))
    a = apply_mask_make_transparent(a, mask)
    b = apply_mask_make_transparent(b, mask)
    b = np.roll(b, 77, axis=1)
    b[:, :77] = 0

    fig, axs = plt.subplots(1, 2)
    axs[0].imshow(a)
    axs[1].imshow(b)
    plt.show()
    print(compare_images_alpha_overlap(a, b))
