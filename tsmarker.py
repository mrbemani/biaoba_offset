# the marker class and marker manager

import cv2
import numpy as np
import target

# the marker class
class TSMarker:
    def __init__(self, marker_id: int, marker_name: str, marker_roi: tuple = None):
        self.marker_id = marker_id
        self.marker_name = marker_name
        if type(marker_roi) not in [tuple, list]:
            self.marker_roi = None
        elif len(marker_roi) != 4 or \
             marker_roi[0] < 0 or marker_roi[1] < 0 or \
             marker_roi[2] < 0 or marker_roi[3] < 0 or \
             marker_roi[0] > input_image.shape[1] or \
             marker_roi[1] > input_image.shape[0]:
            self.marker_roi = None
        else:
            self.marker_roi = marker_roi
        self.ellipse = None
        self.bounding_box = None
        self.marker_image = None

    def find_marker(self, input_image: np.ndarray):
        ret, input_image_thresh = cv2.threshold(self.input_image, 60, 255, cv2.THRESH_BINARY)
        # find input contours
        contours, hierarchy = cv2.findContours(input_image_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # find the biggest area
        cnt = contours[0]
        
        # find the bounding rectangle
        x1, y1, w, h = cv2.boundingRect(cnt)

        # expand area by 10%, make sure it doesn't go out of bounds
        x1 = max(0, int(x1 - w * 0.1))
        y1 = max(0, int(y1 - h * 0.1))
        w = min(self.input_image.shape[1] - x1, int(w * 1.2))
        h = min(self.input_image.shape[0] - y1, int(h * 1.2))

        # find bounding ellipse
        ellipse = cv2.fitEllipse(cnt)

        return ellipse, (x1, y1, w, h)

    def update_marker(self, input_image: np.ndarray):
        self.input_image = input_image
        self.ellipse, self.bounding_box = self.find_marker(input_image)
        self.marker_image = self.crop_marker()

    def perform_compare(self, input_image: np.ndarray):
        # find the marker in the input image
        self.update_marker(input_image)
        # crop the marker
        marker_image = self.crop_marker()
        # compare the marker
        movement = target.perform_compare(self.marker_image, marker_image)
        # calculate the distance
        distance = target.calculate_distance(movement)
        # calculate the gaussian weights
        weights = target.calculate_gaussian_weights(movement)
        # calculate the weighted mean
        weighted_mean = target.calculate_weighted_mean(distance, weights)
        # calculate the average distance
        average_distance = target.calculate_average_distance(distance)
        return average_distance

    def crop_marker(self):
        x1, y1, w, h = self.bounding_box
        return self.input_image[y1:y1+h, x1:x1+w]

    def get_marker_id(self):
        return self.marker_id

    def get_marker_image(self):
        return self.marker_image

    def get_marker_ellipse(self):
        return self.ellipse

    def get_marker_bounding_box(self):
        return self.bounding_box