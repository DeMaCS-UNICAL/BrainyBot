import cv2


def getImg(file, channel=None):
    try:
        if channel is None:
            im = cv2.imread(file)
        else:
            im = cv2.imread(file, channel)
        return im
    except:
        raise Exception(f"NO {file} FOUND. \n")
