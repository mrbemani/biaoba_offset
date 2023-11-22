
import sys
import os
import cv2
import numpy as np
from scipy.optimize import minimize, differential_evolution, least_squares
import matplotlib.pyplot as plt
import avgpixel

# ---------------------------------------------------------------

print ("Loading images ... ", end='', flush=True)
#input_base_path = "../bb/avg/" + sys.argv[1]
#input_image_files = [os.path.join(input_base_path, x) for x in os.listdir(input_base_path) if x.endswith(".bmp")]
# Load the main image and the template image
#input_images = [cv2.imread(x, 0) for x in input_image_files]
#main_image_o = avgpixel.average_image_gray(input_images)
main_image_o = cv2.imread("../bb/"+sys.argv[1], 0)
main_image_o = cv2.resize(main_image_o, (main_image_o.shape[1]*2, main_image_o.shape[0]*2))
template = cv2.imread('marker_33.png', 0)

print ("OK")

# ---------------------------------------------------------------

# load camera intrinsics from yaml
def load_camera_intrinsics():
    fs = cv2.FileStorage("..\\cam\\calib_80mm_x_80mm.yml", cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise FileNotFoundError("Could not open the camera intrinsics file.")

    camera_matrix = fs.getNode("Intrinsics").mat()
    dist_coeffs = fs.getNode("Distortion").mat()
    fs.release()
    
    return camera_matrix, dist_coeffs

cameraMatrix, distCoeffs = load_camera_intrinsics()

# ---------------------------------------------------------------

print ("Applying Binarization ... ", end='', flush=True)
# threshold
ret, main_image = cv2.threshold(main_image_o, 20, 255, cv2.THRESH_BINARY)

print ("OK")

# ---------------------------------------------------------------

print ("Finding bounding box ... ", end="", flush=True)

# find contours
contours, hierarchy = cv2.findContours(main_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# find the biggest area
cnt = contours[0]
max_area = cv2.contourArea(cnt)
for cont in contours:
    if cv2.contourArea(cont) > max_area:
        cnt = cont
        max_area = cv2.contourArea(cont)

# find the bounding rectangle
x1, y1, w, h = cv2.boundingRect(cnt)
x2 = x1 + w
y2 = y1 + h

# find bounding ellipse
ellipse = cv2.fitEllipse(cnt)

print ("OK")

# ---------------------------------------------------------------

print ("Applying mask ... ", end="", flush=True)

# paste this rectangle on a pure black image
black_image = np.zeros(main_image.shape, dtype=np.uint8)
white_image = np.ones(main_image.shape, dtype=np.uint8) * 255
# fill the rectangle on the black image with white
mask_image = cv2.ellipse(black_image, ellipse, (255, 255, 255), -1)

main_image_masked = cv2.bitwise_and(main_image_o, main_image_o, mask=mask_image)

print ("OK")

# ---------------------------------------------------------------

#cv2.imshow("Masked Image", cv2.resize(main_image_masked, (main_image.shape[1]//4, main_image.shape[0]//4)))

# equalize hist to improve contrast
main_image = cv2.equalizeHist(main_image_masked)

# threshold again to remove noise and make it binary
# main_image = cv2.adaptiveThreshold(main_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
ret, main_image = cv2.threshold(main_image, 60, 255, cv2.THRESH_BINARY_INV)

# dilate
kernel = np.ones((3, 3), np.uint8)
main_image = cv2.erode(main_image, kernel, iterations=1)


template = 255 - template

# fill rest with white
main_image = cv2.floodFill(main_image, None, (0, 0), 0)[1]

print ("Fitting template to image ... ", end="", flush=True)

def create_transformation_matrix(params):
    sx, sy, theta, tx, ty = params
    ih, iw = main_image.shape[:2]
    
    M = np.array([
        [sx * np.cos(theta), -sy * np.sin(theta), tx],
        [sx * np.sin(theta),  sy * np.cos(theta), ty],
        [0, 0, 1]
    ])

    return M


def get_hull_and_rotbox(image):
    # get rotated bounding box of white pixels in the main_image
    white_pixels = np.argwhere(image == 255)
    white_pixels = np.fliplr(white_pixels)
    # convex
    hull = cv2.convexHull(white_pixels)
    # rotated bounding box
    rect = cv2.minAreaRect(white_pixels)
    box = cv2.boxPoints(rect)
    box = np.intp(box)
    # reorder box points to : top-left, top-right, bottom-right, bottom-left
    # find top-left point
    min_sum = 999999
    min_idx = 0
    for idx, pt in enumerate(box):
        if pt[0] + pt[1] < min_sum:
            min_sum = pt[0] + pt[1]
            min_idx = idx
    # rotate box
    box = np.roll(box, -min_idx, axis=0)
    # swap points
    if box[0][1] > box[1][1]:
        box[0], box[1] = box[1], box[0]
    if box[2][1] < box[3][1]:
        box[2], box[3] = box[3], box[2]
    return hull, box


target_hull, target_box = get_hull_and_rotbox(main_image)
tpl_hull, tpl_box = get_hull_and_rotbox(template)


target_points = np.array(target_box, dtype="double")

# get homography matrix
H, H_ret = cv2.findHomography(tpl_box, target_box, cv2.RANSAC, 9.0)

# solvePnP to get initial guess
# convert template to 3d points
tpl_box_3d = np.zeros((4, 3), dtype=np.float32)
tpl_box_3d[:, :2] = tpl_box
# solvePnP
retval, rvec, tvec = cv2.solvePnP(tpl_box_3d, target_points, cameraMatrix=cameraMatrix, distCoeffs=distCoeffs, flags=cv2.SOLVEPNP_ITERATIVE)

# Convert rotation vector to rotation matrix
rotation_matrix, _ = cv2.Rodrigues(rvec)

# Convert rotation matrix to Euler angles
euler_angles = cv2.decomposeProjectionMatrix(cv2.hconcat([rotation_matrix, tvec[:3]]))[6]

# Combine rotation matrix and translation vector to form a 3x4 projection matrix
projection_matrix = np.hstack((rotation_matrix, tvec))

# Multiply with camera matrix to get the final perspective transformation matrix
perspective_transform_matrix = np.dot(cameraMatrix, projection_matrix)

def apply_perspective_transform_H(pattern_image, target_img, homography_mat):
    warpflags = cv2.INTER_CUBIC# + cv2.WARP_INVERSE_MAP
    transformed_img = cv2.warpPerspective(pattern_image, homography_mat, (target_img.shape[1], target_img.shape[0]), flags=warpflags, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return transformed_img


loss_history = []

def compute_loss(params):
    transformed_img = apply_perspective_transform_H(template, main_image, params)
    #loss = np.average(((255-transformed_img[y1:y2, x1:x2]) - (255-main_image[y1:y2, x1:x2]))**2)  # Mean Squared Error
    diff = transformed_img.flatten() - main_image.flatten()
    loss = np.sqrt(diff**2)
    #loss_history.append(loss)
    #print(f"Iteration {len(loss_history)}: Loss = {loss}")
    transformed_template = cv2.addWeighted(main_image, 0.5, transformed_img, 0.5, 0)
    cv2.imshow('Matched Areas', cv2.resize(transformed_template, (transformed_template.shape[1]//4, transformed_template.shape[0]//4)))
    cv2.waitKey(1)
    return loss


def callback(params):
    return False


opts = dict(
    maxiter=1000,
    eps=1e-7,
    #finite_diff_rel_step=1e-5,
    #finite_diff_rel_step=None,
    #finite_diff_rel_step=None
)

# draw convex of main_image
#main_image = cv2.cvtColor(main_image, cv2.COLOR_GRAY2BGR)
main_image = cv2.cvtColor(main_image_o, cv2.COLOR_GRAY2BGR)
cv2.drawContours(main_image, [target_hull], 0, (0, 255, 0), 2)

# plot loss history
#cv2.imwrite("target.png", main_image)
# Apply the transformation to the template image
transformed_template = apply_perspective_transform_H(template, main_image, H)
#cv2.imshow("Transformed Template", transformed_template)
cv2.imwrite(sys.argv[2], transformed_template)
# add them together with 50% opacity
transformed_template_bgr = cv2.cvtColor(transformed_template, cv2.COLOR_GRAY2BGR)
transformed_template1 = cv2.addWeighted(main_image, 0.5, transformed_template_bgr, 0.5, 0)
cv2.imshow('Matched Areas', transformed_template1)
#cv2.imshow("Main Image", cv2.resize(main_image, (main_image.shape[1]//4, main_image.shape[0]//4)))
# draw yellow rectangle
# main_image = cv2.cvtColor(main_image, cv2.COLOR_GRAY2BGR)
# cv2.rectangle(main_image, (x1, y1), (x2, y2), (0, 255, 255), 2)

# Display the result
#cv2.imshow('Matched Areas', cv2.resize(main_image, (main_image.shape[1]//4, main_image.shape[0]//4)))  


cv2.waitKey(0)
cv2.destroyAllWindows()

print ("All Done.")
