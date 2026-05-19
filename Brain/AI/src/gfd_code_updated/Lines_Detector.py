import cv2
import numpy as np
import matplotlib.pyplot as plt

def search_lines(image,Hough_params,dilation_params,clustering_threshold, show_imgs=True) -> dict[str, any]:
    '''
    Returns a dictionary with keys:
    - "all_lines_image" - np.ndarray : Image showing all detected lines.
    - "combined_output" - np.ndarray : Image showing final lines after processing.
    - "vertical_coords" - list[int] : List of vertical line coordinates.
    - "horizontal_coords" - list[int] : List of horizontal line coordinates.
    - "removed_lines" - list[int] : List of removed line coordinates.
    - "added_lines" - int : Number of lines added to fill gaps.
    - "covered_area" - int : Area covered by the detected grid.
    '''
    all_lines_image=image.copy()
    dilated_edges = prepare_image(image, dilation_params)

    vertical_lines,horizontal_lines=get_lines(Hough_params, dilated_edges,all_lines_image)

    final_image=image.copy()
    vertical_lines = sorted([(x[0]+x[2])/2 for x in vertical_lines])
    
    horizontal_lines = sorted([(x[1]+x[3])/2 for x in horizontal_lines])

    vertical_median_distance,vertical_lines,removed_vertical_lines = cluster_and_filter_lines(vertical_lines,clustering_threshold)
    horizontal_median_distance,horizontal_lines,removed_horizontal_lines = cluster_and_filter_lines(horizontal_lines,clustering_threshold)
    removed_lines=removed_vertical_lines+removed_horizontal_lines
    if show_imgs:
        draw(final_image,horizontal_lines,0,(0,255,0))
        draw(final_image,vertical_lines,1,(0,255,0))
        plt.imshow(all_lines_image)
        plt.show()
        plt.imshow(final_image)
        plt.show()

    coords = np.argwhere(dilated_edges > 0)   # array of [row, col] pairs
    if coords.size > 0:
        first_row, first_col = coords.min(axis=0)
        last_row,  last_col  = coords.max(axis=0)
    final_image=image.copy()
    complete_vertical_lines = fill_the_gaps(first_col, last_col, vertical_median_distance, vertical_lines)
    complete_horizontal_lines = fill_the_gaps(first_row, last_row, horizontal_median_distance, horizontal_lines)
    added_lines = len(complete_horizontal_lines)-len(horizontal_lines)+len(complete_vertical_lines)-len(vertical_lines)
    if show_imgs:
        draw(final_image,horizontal_lines,0,(0,255,0))
        draw(final_image,vertical_lines,1,(0,255,0))
        draw(final_image,set(complete_horizontal_lines)-set(horizontal_lines),0,(255,0,0))
        draw(final_image,set(complete_vertical_lines)-set(vertical_lines),1,(255,0,0))
    if len(complete_horizontal_lines)>0 and len(complete_vertical_lines)>0:
        covered_area = (complete_horizontal_lines[-1]-complete_horizontal_lines[0])*(complete_vertical_lines[-1]-complete_vertical_lines[0]) 
    else:
        covered_area=0

    return {
        "all_lines_image": all_lines_image,
        "combined_output": final_image,
        "vertical_coords": complete_vertical_lines,
        "horizontal_coords": complete_horizontal_lines,
        "removed_lines": removed_lines,
        "added_lines": added_lines,
        "covered_area": covered_area
    }


def keep_only_straigth( lines:list, all_lines_image):
    
    horizontal=[]
    vertical=[]
    if lines is not None:
        for seg in lines:
            draw=False
            x1,y1,x2,y2 = seg[0]
            theta = np.degrees(np.arctan2(y2-y1, x2-x1))  # from –180° to +180°
            if abs(abs(theta)-90) <1:
                vertical.append(seg[0])
                draw=True
            elif abs(theta)<1:
                horizontal.append(seg[0])
                draw=True
            if draw:
                cv2.line(all_lines_image,(x1,y1),(x2,y2),(0,0,255),2)


    return vertical,horizontal

def get_lines(params, dilated_edges,all_lines_image):
    lines = cv2.HoughLinesP(dilated_edges, 1, np.pi / 180, threshold=int(params["vertical_threshold"]), minLineLength=params["vertical_minLineLength"], maxLineGap=params["vertical_maxLineGap"])
    vertical_lines,horizontal_lines = keep_only_straigth( lines, all_lines_image)
    return vertical_lines,horizontal_lines

def prepare_image(image,params):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    v_channel = hsv_image[:, :, 2]
    _, v_thresh = cv2.threshold(v_channel, params["threshold"], params["maxval"], cv2.THRESH_TOZERO_INV)
    equalized_v = cv2.equalizeHist(v_thresh)
    edges = cv2.Canny(equalized_v, params["canny_thresh"], params["canny_thresh"]*3)
    kernel = np.ones((3, 3), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)
    return dilated_edges

def cluster_and_filter_lines(positions, tolerance):
    
    clustered = []
    temp=[]
    for i in range(len(positions)):
        if len(temp)==0 or positions[i]-temp[-1]<tolerance:
            temp.append(positions[i])
        else:
            clustered.append(int(np.median(temp)))
            temp=[positions[i]]
        if i==len(positions)-1:
            clustered.append(int(np.median(temp)))
    positions = clustered
    distances = np.diff(positions)
    if len(distances)%2==0:
        distances = np.append(distances, np.inf)
    median_distance = np.median(distances)
    positions_filtered = set()  
    for i in range(0, len(positions)):
        for j in range(0, len(positions)):
            if i!=j:
                mod = abs( positions[i] - positions[j]) % median_distance
                div = abs( positions[i] - positions[j]) // median_distance
                if mod< tolerance/5*(div+1):
                    positions_filtered.add(positions[i])
                    positions_filtered.add(positions[j])
                    
    positions_filtered = sorted(positions_filtered)
    return np.median(np.diff(positions_filtered)),positions_filtered,len(positions)-len(positions_filtered)

def fill_the_gaps(start_from_orig, end_to, median_distance, positions_filtered,tolerance=0.2):
    created=[]
    start_from=start_from_orig
    fill_the_center(median_distance, positions_filtered, created, start_from,tolerance)

    add_head(start_from_orig, median_distance, created,tolerance)
    add_tail(end_to, median_distance, tolerance, created)
    return sorted(created)

def add_tail(end_to, median_distance, tolerance, created):
    if len(created)==0:
        return
    div = int((end_to-created[-1])/median_distance)
    mod = (end_to-created[-1])%median_distance
    if div>0 or median_distance-mod<median_distance*tolerance:
        to_add=div
        to_add += 1 if median_distance-mod<median_distance*tolerance else 0
        while to_add>0:
            gap = median_distance if to_add>1 else min(median_distance,end_to-created[-1])
            adding = int(created[-1]+gap)
            created.append(adding)
            to_add -= 1

def add_head(start_from_orig, median_distance, created,tolerance):
    if len(created)==0:
        return
    div = int((created[0]-start_from_orig)/median_distance)
    mod = (created[0]-start_from_orig)%median_distance
    if div==1 or median_distance-mod<median_distance*tolerance:
        adding = int(created[0]-min(median_distance,created[0]-start_from_orig))
        created.insert(0,adding)

def fill_the_center(median_distance, positions_filtered, created, start_from,tolerance):
    for i in range(len(positions_filtered)):
        temp_end=positions_filtered[i]
        div = int((temp_end-start_from)/median_distance)
        mod = (temp_end-start_from)%median_distance
        if div>1 or median_distance-mod<median_distance*tolerance:
            to_add=div-1
            to_add += 1 if median_distance-mod<median_distance*tolerance else 0
            while to_add>0:
                adding = int(temp_end-to_add*median_distance)
                created.append(adding)
                to_add -= 1
        created.append(temp_end)
        start_from=temp_end

def draw(image,lines,axis,color):
    h,w,_=image.shape
    for l in lines:
        start = (l, 0) if axis==1 else (0,l)
        to =(l, h - 1) if axis==1 else (w-1,l)
        cv2.line(image,start,to,color,2)
