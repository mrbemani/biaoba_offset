
import cv2
import numpy as np
import random

# Load the template image
template_image_path = 'marker_33.png'  # Replace with your image path
template_image = cv2.imread(template_image_path)

TPL_H, TPL_W = template_image.shape[:2]
TARGET_W, TARGET_H = 5472, 3648

# load camera intrinsics from cam/iphone13mini_calib.yml
def load_camera_intrinsics():
    fs = cv2.FileStorage("..\\cam\\calib_80mm_x_80mm.yml", cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise FileNotFoundError("Could not open the camera intrinsics file.")

    camera_matrix = fs.getNode("Intrinsics").mat()
    dist_coeffs = fs.getNode("Distortion").mat()
    fs.release()
    
    return camera_matrix, dist_coeffs

# Define camera intrinsics (example values)
camera_matrix, distortion_coefficients = load_camera_intrinsics()

# Function to generate a random homography matrix
def create_transformation_matrix(scale_x, scale_y, theta, tx, ty, skwx, skwy):
    M = np.array([
        [scale_x * np.cos(theta), -scale_y * np.sin(theta), tx],
        [scale_x * np.sin(theta),  scale_y * np.cos(theta), ty],
        [skwx, skwy, 1]
    ])

    return M

def random_homography():
    scale_x = random.uniform(0.03, 0.2)
    scale_y = scale_x*random.uniform(0.9, 1.1)
    theta = random.gauss(0, 0.3)
    tx = random.uniform(TPL_W*scale_x*2, TARGET_W-scale_x*TPL_W*2)
    ty = random.uniform(TPL_H*scale_y*2, TARGET_H-scale_y*TPL_H*2)
    skwx = random.gauss(0, 0.000001)
    skwy = skwx*random.gauss(1.0, 0.05)
    return create_transformation_matrix(scale_x, scale_y, theta, tx, ty, skwx, skwy), (scale_x, scale_y, theta, tx, ty, skwx, skwy)

import numpy as np
import cv2

def project_pattern(pattern, theta_x, theta_y, theta_z, translate_x, translate_y, translate_z, intrinsic_matrix, distortion_coeffs):
    # Define the rotation matrices
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(theta_x), -np.sin(theta_x)],
        [0, np.sin(theta_x), np.cos(theta_x)]
    ])
    rot_y = np.array([
        [np.cos(theta_y), 0, np.sin(theta_y)],
        [0, 1, 0],
        [-np.sin(theta_y), 0, np.cos(theta_y)]
    ])
    rot_z = np.array([
        [np.cos(theta_z), -np.sin(theta_z), 0],
        [np.sin(theta_z), np.cos(theta_z), 0],
        [0, 0, 1]
    ])

    # Combine the rotation matrices
    rotation_matrix = rot_z @ rot_y @ rot_x

    # Create the translation vector
    translation_vector = np.array([translate_x, translate_y, translate_z])

    # Apply rotation and translation to the pattern points
    transformed_points = np.dot(rotation_matrix, pattern.T).T + translation_vector

    # Project the 3D points onto the 2D image plane
    projected_points, _ = cv2.projectPoints(transformed_points, rotation_matrix, translation_vector, intrinsic_matrix, distortion_coeffs)

    # Flatten the points to 2D
    projected_points_2d = projected_points.reshape(-1, 2)

    return projected_points_2d



try:
    for i in range(100):
        # Generate a random perspective transformation
        homography_matrix, params = random_homography()

        # Apply the perspective transformation
        transformed_image = cv2.warpPerspective(template_image, homography_matrix, (TARGET_W, TARGET_H), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

        # Optionally, undistort the image using the camera intrinsics and distortion matrix
        undistorted_image = 255 - transformed_image
        # undistorted_image = cv2.undistort(transformed_image, camera_matrix, distortion_coefficients)

        # putText params
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 2
        color = (0, 255, 0)
        thickness = 6
        cv2.putText(undistorted_image, f"scale_x: {params[0]:.7f}", (50, 100), font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(undistorted_image, f"scale_y: {params[1]:.7f}", (50, 200), font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(undistorted_image, f"theta: {params[2]:.7f}", (50, 300), font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(undistorted_image, f"tx: {params[3]:.7f}", (50, 400), font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(undistorted_image, f"ty: {params[4]:.7f}", (50, 500), font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(undistorted_image, f"skwx: {params[5]:.7f}", (50, 600), font, fontScale, color, thickness, cv2.LINE_AA)
        cv2.putText(undistorted_image, f"skwy: {params[6]:.7f}", (50, 700), font, fontScale, color, thickness, cv2.LINE_AA)

        # Save or display the result
        cv2.imshow('Transformed Image', cv2.resize(undistorted_image, (undistorted_image.shape[1]//4, undistorted_image.shape[0]//4)))
        k = cv2.waitKey(0)
        if k == ord('q'):
            break
except KeyboardInterrupt as kbi:
    print("KeyboardInterrupt")
finally:
    cv2.destroyAllWindows()
