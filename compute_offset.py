import cv2
import numpy as np

def compute_fov(camera_matrix, image_size):
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    w = image_size[1]
    h = image_size[0]
    
    fov_x_rad = 2 * np.arctan(w / (2 * fx))
    fov_y_rad = 2 * np.arctan(h / (2 * fy))
    
    # Convert from radians to degrees
    fov_x_deg = np.degrees(fov_x_rad)
    fov_y_deg = np.degrees(fov_y_rad)
    
    return fov_x_deg, fov_y_deg


def compute_focal_length(camera_matrix, image_size):
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    w = image_size[1]
    h = image_size[0]
    
    focal_length_x = fx * w / 2
    focal_length_y = fy * h / 2
    
    return focal_length_x, focal_length_y


def compute_principal_point(camera_matrix, image_size):
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]
    w = image_size[1]
    h = image_size[0]
    
    principal_point_x = cx * w
    principal_point_y = cy * h
    
    return principal_point_x, principal_point_y


def compute_skew(camera_matrix):
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    skew = camera_matrix[0, 1]
    
    return skew


def load_camera_matrix(filename):
    cv_file = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
    camera_matrix = cv_file.getNode("Intrinsics").mat()
    cv_file.release()
    
    return camera_matrix