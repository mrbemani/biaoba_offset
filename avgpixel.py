

import cv2
import numpy as np

# get average image from a list of grayscale images
def average_image_gray(images):
    images = np.array(images)
    avg_image = np.mean(images, axis=0)
    avg_image = np.array(avg_image, dtype=np.uint8)
    return avg_image

# get average image from a list of color images
def average_image_color(images):
    images = np.array(images)
    avg_image = np.mean(images, axis=0)
    avg_image = np.array(avg_image, dtype=np.uint8)
    return avg_image

# get average image from a list of images
def average_image(images):
    if len(images[0].shape) == 2:
        return average_image_gray(images)
    else:
        return average_image_color(images)

