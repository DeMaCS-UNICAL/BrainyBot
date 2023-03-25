import cv2


def get_img(file):
    try:
        im = cv2.imread(file)
        return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    except:
        raise Exception(f"NO {file} FOUND. \n")
