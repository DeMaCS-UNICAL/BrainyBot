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

def invert_mask_alpha_channel(img: np.ndarray | Image.Image) -> np.ndarray:
    """
    Inverts the alpha channel of an RGBA image.
    Accepts either a numpy array or a PIL Image and returns a numpy array (int32).
    255 (opaque) becomes 0 (transparent) and viceversa.
    """
    # convert PIL Image to numpy int32 (helper to_int32 is defined in the module)
    if isinstance(img, Image.Image):
        res = to_int32(img)
    else:
        res = img.copy()

    # If grayscale or single-channel, nothing to invert
    if res.ndim == 2:
        return res

    # If RGB (3 channels), no alpha to invert
    if res.shape[2] != 4:
        return res

    # Ensure integer type to avoid underflow on subtraction
    if res.dtype != np.int32:
        res = res.astype(np.int32)

    res[:, :, 3] = 255 - res[:, :, 3]
    return res


# Stuff I like to use
def to_rgba(arr: np.ndarray, h: int, w: int) -> np.ndarray:
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=2)
    match arr.shape[2]:
        case 4: return to_int32(arr)
        case 3:
            alpha = np.full((h, w, 1), 255, dtype=arr.dtype)
            return to_int32(np.concatenate([arr, alpha], axis=2))
    raise ValueError("Unsupported channel count")

def to_grayscale(arr: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    return cv2.cvtColor(to_uint8(to_rgba(arr, h, w)), cv2.COLOR_RGBA2GRAY)

def to_uint8(arr: np.ndarray | Image.Image) -> np.ndarray:
    if isinstance(arr, Image.Image):
        arr = to_int32(arr)
    a = np.array(arr, copy=False)
    if a.dtype != np.uint8:
        a = np.clip(a, 0, 255).astype(np.uint8)
    return a

def to_int32(arr: np.ndarray | Image.Image) -> np.ndarray:
    match isinstance(arr, Image.Image):
        case True: return np.array(arr, dtype=np.int32)
        case False: return arr.astype(np.int32)
    raise ValueError("Unsupported type") #I'm proud of myself, a raised exception!!! what a well written piece of code 😂


# Overlap similarity
def np_absolute_distance_image_comparison(img0: Image.Image | np.ndarray, img1: Image.Image | np.ndarray) -> tuple[float, int]:
    """
    img0, img1: images to compare (PIL Image or numpy array)
    return: (mean absolute distance, number of considered pixels)
    0 = identical images
    """
    img0 = to_int32(img0)
    img1 = to_int32(img1)
    if img0.shape[:2] != img1.shape[:2]:
        raise ValueError("Images must have the same dimensions")

    h, w = img0.shape[:2]
    # rgb images will break stuff so do not remove this piece of code, we need them rgba
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

class SimilarityThread(Thread):
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

def check_benchmarked_similarity_algorithms(threads: list[SimilarityThread]) -> None:
    def find_min(scores):
        min_score = float("inf") #if we use scores[0] it will raise an error if list is empty, just thia voids useless checks
        for s in scores:
            if s < min_score:
                min_score = s
        return min_score

    # # average times and best scores for each method
    
    for i, t in enumerate(threads):
        time = sum((t.times[i] for t in threads), datetime.timedelta()) / len(threads)
        score = find_min([t.scores[i] for t in threads])
        shift = [t.shift for t in threads if t.scores[0] == score][0]
        logger.debug(f"Method {i}:\t{shift},\t{score},\t{time}")


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

        t = SimilarityThread(img0, crop1, shift)
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


def find_offset_orb(img0, img1, mask=None, used_detector: int = 0):
    """
    Finds the offset between two images using feature matching with keypoints.

    This function calculates the relative offset (translation in x and y directions)
    between two input images by detecting keypoints and matching them, using one of
    several feature detection techniques. Optionally, a mask can be provided to
    focus on certain regions for keypoint detection and matching.

    [WARNING] do not apply the mask before the step, pass the whole images and the mask here
    you will be held accountable for the problems you cause by not using the mask correctly

    Parameters:
        img0: The first input image as a numpy array.
        img1: The second input image as a numpy array, which will be compared to the first.
        mask: Optional. A mask as a numpy array where non-zero values indicate regions to
              focus on for keypoint detection and matching.
        used_detector: An integer representing the detector to use. Defaults to 0.
                       Acceptable values are:
                       - 0: ORB
                       - 1: AKAZE
                       - 2: SIFT

    Returns:
        A tuple (dx, dy, confidence):
            - dx: float, the estimated x offset between the two images.
            - dy: float, the estimated y offset between the two images.
            - confidence: float, a value between 0 and 1 indicating the confidence
                          of the estimated offset based on inliers and the total
                          number of matches.
                          
    Notes:
        - I hate python indentation
        - another viable detector is fast(brief) but it's not a drop in replacement like the one supported
    """
    
    # This is the implementation of fast, but it's more code to allow for this to be switchable
    # so it's not worth it, if you need this it's easy to implement
    # it's this way because fast does not have a descriptor included so we have to provide it ourself
    # fast = cv2.FastFeatureDetector_create()
    # brief = cv2.xfeatures2d.BriefDescriptorExtractor_create()
    # kp0 = fast.detect(img0, mask_cv)
    # kp1 = fast.detect(img1, mask_cv)
    # kp0, des0 = brief.compute(img0_gray, kp0)
    # kp1, des1 = brief.compute(img1_gray, kp1)
    
    match used_detector:
        case 0: detector = cv2.ORB_create() #nfeatures=2000
        case 1: detector = cv2.AKAZE_create()
        case 2: detector = cv2.SIFT_create() #nfeatures=2000
        case _: detector = cv2.ORB_create() #nfeatures=2000
    
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
    
    kp0, des0 = detector.detectAndCompute(img0_gray, mask_cv)
    kp1, des1 = detector.detectAndCompute(img1_gray, mask_cv)
    
    if des0 is None or des1 is None:
        return 0, 0, 0
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    match used_detector:
        case 0, 1, _: bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        case 2: bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
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

def visualize_orb_matches(img0, img1, mask=None, used_detector: int = 0):
    match used_detector:
        case 0:detector = cv2.ORB_create(nfeatures=2000)
        case 1:detector = cv2.AKAZE_create()
        case 2:detector = cv2.SIFT_create(nfeatures=2000)
        case _:detector = cv2.ORB_create(nfeatures=2000)
    
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
    kp0, des0 = detector.detectAndCompute(img0_gray, mask_cv)
    kp1, des1 = detector.detectAndCompute(img1_gray, mask_cv)
    
    if des0 is None or des1 is None:
        return cv2.drawMatches(img0, [], img1, [], [], None), (0, 0)
    
    match used_detector:
        case 0: bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        case 1: bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        case 2: bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        case _: bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
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
    confidence = np.sum(inliers) / len(matches) if len(matches) > 0 else 0
    return vis_img, (dx, dy, confidence)


def show_image_full_resolution(img: Image.Image | np.ndarray, title: str | None = None, dpi: int = 100, max_inches: float = 16.0):
    """
    Display a PIL Image or numpy array in a matplotlib window attempting to preserve full image resolution.
    Needed because using pycharm with remote deevelopment on wsl only matplotlib appears so I need this

    Behavior:
    - If possible, opens a figure whose pixel dimensions match the image (1:1 mapping) by setting
      figsize = (width/dpi, height/dpi) and figure dpi.
    - If the resulting window would be larger than `max_inches` on the longest side, the image is
      uniformly downscaled to fit within that constraint to avoid creating an enormous window.
    - Uses interpolation='nearest' to avoid smoothing and preserve pixel-perfect rendering.

    Parameters:
        img: PIL.Image.Image or numpy.ndarray
        title: optional window title
        dpi: DPI used for the matplotlib figure
        max_inches: maximum inches allowed for the longest figure side
    """

    if isinstance(img, Image.Image):
        arr = np.array(img)
    else:
        arr = img

    if arr is None:
        raise ValueError("No image provided")

    if arr.ndim == 2:
        h, w = arr.shape
    else:
        h, w = arr.shape[:2]

    max_px_allowed = int(dpi * max_inches)
    scale = 1.0
    if max(h, w) > max_px_allowed:
        scale = max_px_allowed / max(h, w)

    display_w = max(1, int(w * scale))
    display_h = max(1, int(h * scale))

    figsize = (display_w / dpi, display_h / dpi)

    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(1, 1, 1)
    ax.imshow(arr, interpolation='nearest')
    ax.axis('off')
    if title:
        ax.set_title(title)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.show()


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
    b = np.array(Image.open("test_material/single_axis/screenshot_0.png"))
    # a = apply_mask_make_transparent(a, mask)
    # b = apply_mask_make_transparent(b, mask)
    # b = np.roll(b, 77, axis=1)
    # b[:, :77] = 0
    x_movement = 130
    y_movement = 130
    b = np.roll(b, x_movement, axis=1)
    b = np.roll(b, y_movement, axis=0)
    # b[:, :x_movement] = 0
    # b[:y_movement, :] = 0

    # Show the two images at (nearly) full resolution. If they're extremely large, they will be
    # uniformly scaled down so the longest side fits within `max_inches` inches on screen.
    # show_image_full_resolution(a, title="Original", dpi=100, max_inches=16.0)
    # show_image_full_resolution(b, title=f"Shifted ({x_movement}px,{y_movement}px)", dpi=100, max_inches=16.0)

    for i in range(3):
        start = datetime.datetime.now()
        img, res = visualize_orb_matches(a, b, mask, i)
        print(datetime.datetime.now() - start, res)
        Image.fromarray(img).save(f"matches_{i}.png")
        # visualize orb matches (may be large) using our helper
        # show_image_full_resolution(img, title=f"ORB matches detector {i}", dpi=100, max_inches=16.0)
    
