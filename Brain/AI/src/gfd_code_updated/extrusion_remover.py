import numpy as np


def process_image(img, threshold=100):
    img_array = img.copy()  
    if img_array.ndim == 2:
        nonblack = img_array != 0                 # (H,W)
    else:
        nonblack = np.any(img_array != 0, axis=2) # (H,W)

    H, W = nonblack.shape

    row_counts = np.count_nonzero(nonblack, axis=1)           # (H,)
    row_hits = np.flatnonzero(row_counts > threshold)

    if row_hits.size == 0:
        img_array[...] = 0
        return img_array

    top = row_hits[0]
    bottom = row_hits[-1]

    if top > 0:
        img_array[:top, :] = 0
    if bottom + 1 < H:
        img_array[bottom+1:, :] = 0


    col_counts = np.count_nonzero(nonblack, axis=0)           # (W,)
    col_hits = np.flatnonzero(col_counts > threshold)

    if col_hits.size == 0:
        img_array[...] = 0
        return img_array

    left = col_hits[0]
    right = col_hits[-1]

    if left > 0:
        img_array[:, :left] = 0
    if right + 1 < W:
        img_array[:, right+1:] = 0

    return img_array

