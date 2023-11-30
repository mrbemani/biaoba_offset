
import cv2
import numpy as np

def find_marker(input_image: np.ndarray):
    ret, input_image_thresh = cv2.threshold(input_image, 60, 255, cv2.THRESH_BINARY)
    # find input contours
    contours, hierarchy = cv2.findContours(input_image_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    # find the biggest area
    cnt = contours[0]
    
    # find the bounding rectangle
    x1, y1, w, h = cv2.boundingRect(cnt)

    # find bounding ellipse
    ellipse = cv2.fitEllipse(cnt)

    return ellipse, (x1, y1, w, h)
