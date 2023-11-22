# -*- encoding: utf-8 -*-
# Demonstrates how to find the normal vector of a marker in an image

__author__ = 'Mr.Bemani'


import cv2
import numpy as np

# Load image
image = cv2.imread('path_to_image.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Camera intrinsics matrix
intrinsics = np.array([
   [2.0732592956367906e+04, 0., 2.7537088954443120e+03],
   [0., 2.0688824190191150e+04, 2.2924074326704267e+03],
   [0., 0., 1.]
], dtype=np.float64)

# Distortion coefficients
distortion = np.array([
   -3.1061568292327224e-01, 
   3.8916871254822745e+01,
   5.0771971557899490e-03, 
   -1.9050305893242422e-03,
   -1.1620912124203378e+03 
], dtype=np.float64)

# Define the number of inner corners per a chessboard row and column
num_corners_hor = 7  # adjust this to your checkerboard
num_corners_ver = 5  # adjust this to your checkerboard
square_size = 0.02  # actual size of the squares on your marker (in meters or the unit you prefer)

# Prepare the object points (like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0))
objp = np.zeros((num_corners_hor*num_corners_ver, 3), np.float32)
objp[:,:2] = np.mgrid[0:num_corners_hor, 0:num_corners_ver].T.reshape(-1,2)
objp *= square_size

# Find the checkerboard corners
ret, corners = cv2.findChessboardCorners(gray, (num_corners_hor, num_corners_ver), None)

# If found, add object points, image points (after refining them)
if ret:
    # Refine corner location to subpixel accuracy
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    corners_subpix = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

    # Find the rotation and translation vectors using solvePnP
    _, rvecs, tvecs = cv2.solvePnP(objp, corners_subpix, intrinsics, distortion)

    # Convert rotation vector to a rotation matrix
    R, _ = cv2.Rodrigues(rvecs)

    # Draw the normal vector from the center of the marker
    normal = R[:, 2]  # Third column of rotation matrix
    center_point_3d = np.mean(objp, axis=0)  # The 3D center of the marker
    normal_end_point_3d = (normal * square_size * 2) + center_point_3d  # Extend the normal outwards from the center
    
    # Project the 3D center and normal end point back onto the image plane
    center_point_2d, _ = cv2.projectPoints(np.array([center_point_3d]), rvecs, tvecs, intrinsics, distortion)
    end_point_2d, _ = cv2.projectPoints(np.array([normal_end_point_3d]), rvecs, tvecs, intrinsics, distortion)
    
    # Draw the normal vector on the image as a line
    image = cv2.line(image, tuple(center_point_2d[0].ravel()), tuple(end_point_2d[0].ravel()), (255, 255, 0), 3)

    # Display the image
    cv2.imshow('Image with marker normal', image)
    cv2.waitKey(0)

cv2.destroyAllWindows()
