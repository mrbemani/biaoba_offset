
import cv2
import numpy as np
from scipy.optimize import minimize, differential_evolution, least_squares
import matplotlib.pyplot as plt


def find_marker(input_image: np.ndarray, marker_input: np.ndarray):
    ret, input_image_thresh = cv2.threshold(input_image, 60, 255, cv2.THRESH_BINARY)
    # marker canny
    marker_canny = cv2.Canny(marker_input, 100, 200)
    # find marker contours
    marker_contours, marker_hierarchy = cv2.findContours(marker_canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # find the biggest marker contour area
    marker_contours = sorted(marker_contours, key=cv2.contourArea, reverse=True)
    marker_cnt = marker_contours[0]
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

"""
def fit_marker(marker_input: np.ndarray, input_image: np.ndarray, ellipse: tuple, x1: int, y1: int, w: int, h: int):
    # paste this rectangle on a pure black image
    black_image = np.zeros(input_image.shape, dtype=np.uint8)
    white_image = np.ones(input_image.shape, dtype=np.uint8) * 255
    # fill the rectangle on the black image with white
    mask_image = cv2.ellipse(black_image, ellipse, (255, 255, 255), -1)

    input_image_masked = cv2.bitwise_and(input_image, input_image, mask=mask_image)
    eq_input_image = cv2.equalizeHist(input_image_masked)
    
    ret, main_image = cv2.threshold(eq_input_image, 60, 255, cv2.THRESH_BINARY_INV)

    # dilate
    kernel = np.ones((3, 3), np.uint8)
    main_image = cv2.erode(main_image, kernel, iterations=1)


    template = 255 - template

    # fill rest with white
    main_image = cv2.floodFill(main_image, None, (0, 0), 0)[1]

    print ("Fitting template to image ... ", end="", flush=True)
"""
