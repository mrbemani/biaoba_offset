# utility functions

__author__ = 'Mr.Bemani'

import cv2
import time
import numpy as np

# find the marker in the input image
def find_marker(input_image: np.ndarray):
    input_image = cv2.equalizeHist(input_image)
    # save
    cv2.imwrite(f"marker_enhanced.jpg", input_image)
    ret, input_image_thresh = cv2.threshold(input_image, 127, 255, cv2.THRESH_BINARY)
    # save
    cv2.imwrite(f"marker_threshold.jpg", input_image_thresh)
    # dilate the image
    kernel = np.ones((3, 3), np.uint8)
    input_image_dilated_thresh = cv2.dilate(input_image_thresh, kernel, iterations=1)
    # save
    cv2.imwrite(f"marker_dilated.jpg", input_image_dilated_thresh)
    # find input contours
    contours, hierarchy = cv2.findContours(input_image_dilated_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    # find the biggest area
    cnt = contours[0]
    
    # find the bounding rectangle
    x1, y1, w, h = cv2.boundingRect(cnt)

    # expand area by 10%, make sure it doesn't go out of bounds
    x1 = max(0, int(x1 - w * 0.1))
    y1 = max(0, int(y1 - h * 0.1))
    w = min(input_image.shape[1] - x1, int(w * 1.2))
    h = min(input_image.shape[0] - y1, int(h * 1.2))

    # if the area is too small, return None
    if w < 32 or h < 32:
        print (f"Area too small: {w}, {h}")
        return None, None

    try:
        # find bounding ellipse
        ellipse = cv2.fitEllipse(cnt)
    except:
        ellipse = ((w/2, h/2), (w/2, h/2), 0)

    return ellipse, (x1, y1, w, h)



