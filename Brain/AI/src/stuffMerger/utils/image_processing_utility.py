import datetime
import logging
from logging import DEBUG
from threading import Thread

import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from AI.src.constants import logger
from AI.src.stuffMerger.enums import Direction, Orientation

# Conversions functions
def apply_mask_make_transparent(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    img: input image (H,W,3) or (H,W,4) or (H,W) ~ RGB or RGBA or grayscale
    mask: input mask (H,W,3) or (H,W,4) or (H,W) ~ RGB or RGBA or grayscale
    STRONGLY RECOMMENDED to use RGBA (H,W,4) mask with alpha channel, you can generate one from a black and white image
        with make_alpha_mask_from_bw function
    return: image with alpha channel applied according to the mask
    1) if the mask pixel is white (255,255,255) the corresponding image pixel is kept
    2) if the mask pixel alpha channel is 255 the corresponding image pixel is kept
    3) otherwise the corresponding image pixel is made transparent
    """
    h, w = img.shape[:2]
    img_rgba = to_rgba(img, h, w)
    m = np.array(mask)

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

    # This way we can try and fix the mask if the resolution is different but this should not happen normally
    if mask_keep.shape != (h, w):
        logger.warning("The mask has a different shape than the image, it will be resized using nearest neighbor")
        """
        https://medium.com/@epcm18/image-resampling-in-image-processing-f7b597ee78a8
        """
        mask_img = Image.fromarray((mask_keep.astype('uint8') * 255))
        mask_img = mask_img.resize((w, h), resample=Image.Resampling.NEAREST)
        mask_keep = (np.array(mask_img) > 0)

    mask_keep = mask_keep.astype(bool)

    inv = ~mask_keep
    if inv.any():
        img_rgba[inv, :3] = 0
        img_rgba[inv, 3] = 0

    return img_rgba


# Stuff I like to use
def to_rgba(arr: np.ndarray, h: int, w: int) -> np.ndarray:
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=2)
    if arr.shape[2] == 4:
        return arr.astype(np.int32)
    if arr.shape[2] == 3:
        alpha = np.full((h, w, 1), 255, dtype=arr.dtype)
        return np.concatenate([arr, alpha], axis=2).astype(np.int32)
    raise ValueError("Unsupported channel count")

def to_uint8(arr: np.ndarray) -> np.ndarray:
    a = np.array(arr, copy=False)
    if a.dtype != np.uint8:
        a = np.clip(a, 0, 255).astype(np.uint8)
    return a

def to_grayscale(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    return cv2.cvtColor(to_uint8(to_rgba(img, h, w)), cv2.COLOR_RGBA2GRAY)


# Overlap similarity
def np_absolute_distance_image_comparison(img0: Image.Image | np.ndarray, img1: Image.Image | np.ndarray) -> tuple[float, int]:
    """
    img0, img1: images to compare (PIL Image or numpy array)
    return: (mean absolute distance, number of considered pixels)
    0 = identical images
    """
    if isinstance(img0, Image.Image):
        img0 = np.array(img0, dtype=np.int32)
    if isinstance(img1, Image.Image):
        img1 = np.array(img1, dtype=np.int32)
    if img0.shape[:2] != img1.shape[:2]:
        raise ValueError("Images must have the same dimensions")

    h, w = img0.shape[:2]
    # ensure images are not RGB
    img0rgba = to_rgba(img0, h, w)
    img1rgba = to_rgba(img1, h, w)

    # checking the alpha channel we spare only the overlapping pixels with alpha>0 in both images
    # This is not really needed, but it removes some pixels that are not relevant for the comparison
    # alpha_overlap = (img0rgba[:, :, 3] > 0) & (img1rgba[:, :, 3] > 0)
    # n = int(np.count_nonzero(alpha_overlap))
    # if n == 0:
    #     return float("inf"), 0
    # me from the future: apparently this was a waste of performance, so I commented it out, it's going to stay here for
    # history until someone decide it's not needed anymore (commented date:04/11/2025)

    diff = np.abs(img0rgba[:, :, :3].astype(np.float64) - img1rgba[:, :, :3].astype(np.float64)).mean(axis=2)
    # vals = diff[alpha_overlap]
    return float(diff.mean()), np.count_nonzero(diff)

def np_cosine_similarity(img0: np.ndarray, img1: np.ndarray) -> float:
    """
    https://en.wikipedia.org/wiki/Cosine_similarity
    https://www.geeksforgeeks.org/dbms/cosine-similarity/
    Pretty fast but not ideal for offset detection
    """
    picture1_norm = img0 / np.sqrt(np.sum(img0 ** 2))
    picture2_norm = img1 / np.sqrt(np.sum(img1 ** 2))
    return np.sum(picture2_norm * picture1_norm)

def cv2_structural_similarity(img0: np.ndarray, img1: np.ndarray) -> float:
    """
    https://en.wikipedia.org/wiki/Structural_similarity_index_measure
    https://scikit-image.org/docs/0.25.x/auto_examples/transform/plot_ssim.html
    """
    first_gray = to_grayscale(img0)
    second_gray = to_grayscale(img1)
    score, _ = structural_similarity(first_gray, second_gray, full=True)
    return score

def cv2_match_template(img0: np.ndarray, img1: np.ndarray, method=cv2.TM_SQDIFF_NORMED) -> float:
    """
    https://docs.opencv.org/4.11.0/de/da9/tutorial_template_matching.html
    [WARNING] only TM_SQDIFF and TM_CCORR support mask from my understanding
    Notes that SQDIFF is more sensitive to small differences and that include noise, so for noisy images avoid this
    Since we're working with screen and we want the most accuracy possible SQDIFF wins
    CCORR is less sensitive so it's less likely to break on photorealistic environment BUT to use this you need to switch to max_val
    I use the normed one by default you can choose what you want to use but do some research/testing before changing stuff, it's pretty prone to breaking in edge cases
    """
    first_gray = to_grayscale(img0)
    second_gray = to_grayscale(img1)
    res = cv2.matchTemplate(first_gray, second_gray, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return float(np.clip(1.0 - min_val, 0.0, 1.0))

class SimilaritySingleAxisThread(Thread):
    """
    Execute the similarity computation in a separate thread and store the result in self.score
    The comparison algorithms can be changed default one is cv2_match_template that is the fastest
    img0: first image
    img1: second image
    shift: the shift applied to img1 (for logging purposes)
    algorithm: function to use for comparison, should take two numpy arrays as input and return a float score (higher = more similar)
    """
    
    def __init__(self, img0, img1, shift, algorithm=cv2_match_template):
        super().__init__()
        self.img0: np.ndarray = img0
        self.crop1: np.ndarray = img1
        self.shift = shift
        self.score = None
        self.times = []
        self.scores = []
        self.n_valid = None
        self.algorithm = algorithm
    
    def run(self):
        self.score = 1 - self.algorithm(self.img0, self.crop1)
        logger.log(DEBUG, f"Score at shift {self.shift}: old {self.score!r}")
    
    # def execute_and_save_score_and_time(self, algorithm: Callable[[np.ndarray, np.ndarray], float | any]):
    #     time_start = datetime.datetime.now()
    #     self.times.append(datetime.datetime.now() - time_start)
    
    def benchmark_algorithms(self):
        time0 = datetime.datetime.now()
        # ------------ absolute distance ------------
        s1, self.n_valid = np_absolute_distance_image_comparison(self.img0, self.crop1)
        self.n_valid = 10
        time1 = datetime.datetime.now()
        self.times.append(time1 - time0)
        self.scores.append(s1)
        # ------------ cosine similarity ------------
        s2 = 1 - np_cosine_similarity(self.img0, self.crop1)
        time2 = datetime.datetime.now()
        self.times.append(time2 - time1)
        self.scores.append(s2)
        # ------------ structural similarity ------------
        s3 = 1 - cv2_structural_similarity(self.img0, self.crop1)
        time3 = datetime.datetime.now()
        self.times.append(time3 - time2)
        self.scores.append(s3)
        # ------------ template matching ------------ [BEST ONE]
        s4 = 1 - cv2_match_template(self.img0, self.crop1)
        time4 = datetime.datetime.now()
        self.times.append(time4 - time3)
        self.scores.append(s4)

def check_benchmarked_single_axis_algorithms(threads: list[SimilaritySingleAxisThread]) -> None:
    def find_min(scores):
        min_score = float("inf")
        for s in scores:
            if s < min_score:
                min_score = s
        return min_score

    # # average times and best scores for each method
    t1 = sum((t.times[0] for t in threads), datetime.timedelta()) / len(threads)
    t2 = sum((t.times[1] for t in threads), datetime.timedelta()) / len(threads)
    t3 = sum((t.times[2] for t in threads), datetime.timedelta()) / len(threads)
    t4 = sum((t.times[3] for t in threads), datetime.timedelta()) / len(threads)

    score1 = find_min([t.scores[0] for t in threads])
    score2 = find_min([t.scores[1] for t in threads])
    score3 = find_min([t.scores[2] for t in threads])
    score4 = find_min([t.scores[3] for t in threads])

    shift1 = [t.shift for t in threads if t.scores[0] == score1][0]
    shift2 = [t.shift for t in threads if t.scores[1] == score2][0]
    shift3 = [t.shift for t in threads if t.scores[2] == score3][0]
    shift4 = [t.shift for t in threads if t.scores[3] == score4][0]

    logger.log(
        DEBUG,
        f"Time breakdown:\nmethod1 {shift1},{score1},{t1}\nmethod2 {shift2},{score2},{t2}\nmethod3 {shift3},{score3},{t3}\nmethod4 {shift4},{score4},{t4}"
    )


# Offset detection
def cv2_phase_correlation(img0: np.ndarray, img1: np.ndarray) -> tuple[float, float, float]:
    # Not compatible with masks = useless
    # Could try with "Windowing" (Hann Window) basically fading out the edges but the mask still need to be a rectangle
    first_gray = to_grayscale(img0)
    second_gray = to_grayscale(img1)

    img0_32 = np.float32(first_gray)
    img1_32 = np.float32(second_gray)
    
    # This returns ( (x, y), response_strength )
    (dx, dy), response = cv2.phaseCorrelate(img0_32, img1_32)
    
    return dx, dy, response

def cv2_match_template_multi_axis(img0: np.ndarray, img1: np.ndarray, method=cv2.TM_SQDIFF_NORMED) -> tuple[int, int, float]:
    """
    https://docs.opencv.org/4.11.0/de/da9/tutorial_template_matching.html
    Need adjustment, since we want to find the offset this does not work as intented for now
    To make this work we need to check for section of the second image
    """
    first_gray = to_grayscale(img0)
    second_gray = to_grayscale(img1)
    res = cv2.matchTemplate(first_gray, second_gray, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        offset_x, offset_y = min_loc
        # For SQDIFF/SQDIFF_NORMED, 0 is perfect, 1 is terrible.
        confidence = 1.0 - min_val if method == cv2.TM_SQDIFF_NORMED else min_val
    else:
        offset_x, offset_y = max_loc
        # For CCORR/COEFF_NORMED, 1 is perfect, 0 is terrible.
        confidence = max_val
    
    return offset_x, offset_y, float(np.clip(confidence, 0.0, 1.0))

def find_best_offset(
        _img0: Image.Image | np.ndarray,
        _img1: Image.Image | np.ndarray,
        _mask: Image.Image | np.ndarray,
        base_shift: int,
        check_range: tuple[int, int],  # min -> max
        check_step: int,
        direction: Direction = Direction.HORIZONTAL,
        orientation: Orientation = Orientation.DESCENDING
):
    """
    _img0: image to match
    _img1: image to check
    _mask: mask for both images (only check alpha values, can be generated from a black and white image with make_alpha_mask_from_bw)
    base_shift: how much the check image is shifted from the first image (can be negative)
    check_range: range of offset to check (a, b) a->b (a can be negative)
    check_step: how many pixels between each check (1 = every pixel)
    direction: change the direction of the shift (0 = horizontal, 1 = vertical)
    orientation: change the orientation of the shift (basically if the delta is positive or negative)
    """
    if isinstance(_mask, Image.Image):
        _mask = np.array(_mask, dtype=np.int32)
    if isinstance(_img0, Image.Image):
        _img0 = np.array(_img0, dtype=np.int32)
    if isinstance(_img1, Image.Image):
        _img1 = np.array(_img1, dtype=np.int32)
    img0 = apply_mask_make_transparent(_img0, _mask)
    img1 = apply_mask_make_transparent(_img1, _mask)

    best_score = float("inf")
    best_shift = base_shift

    threads = []
    now = datetime.datetime.now()

    for delta in range(check_range[0], check_range[1] + 1, check_step):
        shift = base_shift + (delta if orientation == Orientation.DESCENDING else -delta)

        if direction == Direction.HORIZONTAL:
            crop1 = np.roll(img1, shift, axis=1)
            if orientation == Orientation.DESCENDING:
                crop1[:, :shift] = 0
            else:
                crop1[:, -shift:] = 0
        else:
            crop1 = np.roll(img1, shift, axis=0)
            if orientation == Orientation.DESCENDING:
                crop1[:shift, :] = 0
            else:
                crop1[-shift:, :] = 0

        t = SimilaritySingleAxisThread(img0, crop1, shift)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    logger.log(level=logging.DEBUG, msg=f"Total time{datetime.datetime.now() - now}")

    for t in threads:
        if t.score < best_score:
            best_score = t.score
            best_shift = t.shift
            if best_shift in check_range:
                logger.log(logging.WARNING,
                           f"The shift is at the border of the check_range, probably the search was a failure")

    logger.log(
        DEBUG,
        f"result: {best_shift} {best_score}"
    )

    return best_shift, best_score


def find_offset_orb(img0, img1, mask=None):
    orb = cv2.ORB_create(nfeatures=2000)
    img0_gray = to_grayscale(img0)
    img1_gray = to_grayscale(img1)
    
    # Preprocess mask
    mask_cv = None
    if mask is not None:
        m = np.array(mask)
        h, w = img0_gray.shape
        if m.shape[:2] != (h, w):
            m_img = Image.fromarray(to_uint8(m))
            m_img = m_img.resize((w, h), resample=Image.Resampling.NEAREST)
            m = np.array(m_img)
        
        if m.ndim == 3 and m.shape[2] == 4:
            mask_keep = (np.all(m[:, :, :3] == 255, axis=2)) | (m[:, :, 3] == 255)
        elif m.ndim == 3 and m.shape[2] == 3:
            mask_keep = np.all(m == 255, axis=2)
        else:
            mask_keep = (m != 0)
        mask_cv = mask_keep.astype(np.uint8) * 255
    
    kp0, des0 = orb.detectAndCompute(img0_gray, mask_cv)
    kp1, des1 = orb.detectAndCompute(img1_gray, mask_cv)
    
    if des0 is None or des1 is None:
        return 0, 0, 0
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des0, des1)
    
    if len(matches) < 4:
        logger.warn("Not enough matches found to calculate offset.")
        return 0, 0, 0
    
    src_pts = np.float32([kp0[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp1[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    
    # Find the Translation Matrix (Estimate affine limited to translation)
    # RANSAC filters out points that don't move in the same direction
    matrix, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC)
    
    if matrix is not None:
        # matrix is [[1, 0, tx], [0, 1, ty]]
        dx = matrix[0, 2]
        dy = matrix[1, 2]
        confidence = np.sum(inliers) / len(matches) if len(matches) > 0 else 0
        return dx, dy, confidence
    
    return 0, 0, 0

def visualize_orb_matches(img0, img1, mask=None):
    orb = cv2.ORB_create(nfeatures=2000)
    img0_gray = to_grayscale(img0)
    img1_gray = to_grayscale(img1)

    # Preprocess mask
    mask_cv = None
    if mask is not None:
        m = np.array(mask)
        h, w = img0_gray.shape
        if m.shape[:2] != (h, w):
            m_img = Image.fromarray(to_uint8(m))
            m_img = m_img.resize((w, h), resample=Image.Resampling.NEAREST)
            m = np.array(m_img)
        if m.ndim == 3 and m.shape[2] == 4:
            mask_keep = (np.all(m[:, :, :3] == 255, axis=2)) | (m[:, :, 3] == 255)
        elif m.ndim == 3 and m.shape[2] == 3:
            mask_keep = np.all(m == 255, axis=2)
        else:
            mask_keep = (m != 0)
        mask_cv = mask_keep.astype(np.uint8) * 255
    kp0, des0 = orb.detectAndCompute(img0_gray, mask_cv)
    kp1, des1 = orb.detectAndCompute(img1_gray, mask_cv)
    if des0 is None or des1 is None:
        return cv2.drawMatches(img0, [], img1, [], [], None), (0, 0)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des0, des1)
    matches = sorted(matches, key=lambda x: x.distance)
    if not matches:
        return cv2.drawMatches(img0, kp0, img1, kp1, [], None), (0, 0)
    src_pts = np.float32([kp0[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp1[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    matrix, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC)
    matches_mask = []
    if inliers is not None:
        matches_mask = inliers.ravel().tolist()
    else:
        matches_mask = [0] * len(matches)
    
    matches_to_draw = matches[:50]
    mask_to_draw = matches_mask[:50]
    
    draw_params = dict(matchColor=(0, 255, 0),
                       singlePointColor=None,
                       matchesMask=mask_to_draw,
                       flags=2)
    
    vis_img = cv2.drawMatches(img0, kp0, img1, kp1, matches_to_draw, None, **draw_params)
    dx, dy = (matrix[0, 2], matrix[1, 2]) if matrix is not None else (0, 0)
    return vis_img, (dx, dy)


if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    os.chdir("../resources/")
    print(os.getcwd())
    mask = np.array(Image.open("test_material/islandempire_mask_alpha.png"))
    
    # a = np.array(Image.open("cache/screenshot_0.png"))
    # b = np.array(Image.open("cache/screenshot_0.png"))
    # print(cv2_match_template(a, b))
    #
    # a = np.array(Image.open("cache/screenshot_1.png"))
    # b = np.array(Image.open("cache/screenshot_1.png"))
    # a = apply_mask_make_transparent(a, mask)
    # b = apply_mask_make_transparent(b, mask)
    # print(cv2_match_template(a, b))

    a = np.array(Image.open("test_material/single_axis/screenshot_0.png"))
    b = np.array(Image.open("test_material/single_axis/screenshot_1.png"))
    # a = apply_mask_make_transparent(a, mask)
    # b = apply_mask_make_transparent(b, mask)
    b = np.roll(b, 77, axis=1)
    b[:, :77] = 0

    fig, axs = plt.subplots(1, 3, figsize=(20, 10))
    axs[0].imshow(a)
    axs[1].imshow(b)
    img, _ = visualize_orb_matches(a, b, mask)
    
    # Save full resolution image
    Image.fromarray(img).save("orb_matches_full_res.png")
    
    axs[2].imshow(Image.fromarray(img))
    plt.show()
    print(cv2_match_template(a, b))
    print(find_offset_orb(a, b, mask))
