import cv2


def getImg(file, gray=False,color_conversion=None):
    try:
        
        if not gray:
            im = cv2.imread(file)
        else:
            im = cv2.imread(file,cv2.IMREAD_GRAYSCALE)
        if color_conversion is None:
            return im
        else:
            return cv2.cvtColor(im, color_conversion)
    except:
        raise Exception(f"NO {file} FOUND. \n")
    
def check_in_range(node1: (), node2: (), p: int, approximation) -> bool:
    return node1[p] - approximation <= node2[p] <= node1[p] + approximation

def customExagonalSorter(elements : list):
    return (elements[1], elements[0])
