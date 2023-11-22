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


def compute_focal_length(camera_matrix):
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    return fx, fy


def compute_principal_point(camera_matrix):
    cx = camera_matrix[0, 2]
    cy = camera_matrix[1, 2]
    return cx, cy


def compute_skew(camera_matrix):
    fx = camera_matrix[0, 0]
    fy = camera_matrix[1, 1]
    skew = camera_matrix[0, 1]
    
    return skew


def load_camera_params(filename):
    cv_file = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
    camera_matrix = cv_file.getNode("Intrinsics").mat()
    dist_coeffs = cv_file.getNode("Distortion").mat()
    cv_file.release()
    return camera_matrix, dist_coeffs


def compute_opticalflow(reference_image, target_image):
    # Convert to grayscale
    reference_image_gray = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
    target_image_gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
    
    # Compute optical flow
    flow = cv2.calcOpticalFlowFarneback(reference_image_gray, target_image_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    
    # Compute magnitude and angle of 2D vectors
    magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    
    # create a mask
    mask = np.zeros_like(reference_image)

    # set image hue according to the optical flow direction
    mask[..., 0] = angle * 180 / np.pi / 2

    # set value as per the normalized magnitude of optical flow
    mask[..., 2] = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)

    # convert HSV to RGB
    rgb = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)

    return rgb, magnitude, angle, flow


def fit_ellipse_on_image(image):
    # fit an ellipse on image with subpixel percision
    # Convert to grayscale
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image
    ret, thresh = cv2.threshold(image_gray, 80, 255, 0)

    # fit ellipse onto white pixels
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnt = contours[0]

    cv2.imshow("thresh", cv2.resize(thresh, (0,0), fx=0.3, fy=0.3))
    cv2.waitKey(0)
    print (cnt)
    ellipse = cv2.fitEllipse(cnt)

    # draw ellipse
    image_with_ellipse = cv2.ellipse(image, ellipse, (0, 255, 0), 2)

    # return ellipse
    return image_with_ellipse, ellipse

if __name__ == '__main__':
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Compute Offset use Optical-Flow.")
    parser.add_argument("-c", "--camera_param_file", help="Camera Intrinsics and Distortion-Coefficient.", required=True)
    parser.add_argument("-r", "--reference_image", help="Input directory of images.", required=True)
    parser.add_argument("-t", "--target_image", help="Input directory of images.", required=True)
    parser.add_argument("-o", "--output_image", help="Output directory of images.", required=True)
    args = parser.parse_args()

    reference_image = cv2.imread(args.reference_image)
    target_image = cv2.imread(args.target_image)

    # get actually area in MM^2 based on camera parameters: pixel to mm
    camera_matrix, dist_coeffs = load_camera_params(args.camera_param_file)
    fov_x_deg, fov_y_deg = compute_fov(camera_matrix, reference_image.shape)
    focal_length_x, focal_length_y = compute_focal_length(camera_matrix)
    principal_point_x, principal_point_y = compute_principal_point(camera_matrix)
    skew = compute_skew(camera_matrix)
    actually_area = (reference_image.shape[0] / focal_length_y) * (reference_image.shape[1] / focal_length_x) * (fov_x_deg / reference_image.shape[1]) * (fov_y_deg / reference_image.shape[0])
    area_perpixel = actually_area / (reference_image.shape[0] * reference_image.shape[1])
    length_perpixel = np.sqrt(area_perpixel)

    # print out camera parameters
    print("Camera Parameters:")
    print("    Focal Length: {} x {}".format(focal_length_x, focal_length_y))
    print("    Principal Point: {} x {}".format(principal_point_x, principal_point_y))
    print("    Skew: {}".format(skew))
    print("    FOV: {} x {}".format(fov_x_deg, fov_y_deg))
    print("    Actually Area: {}".format(actually_area))
    print("    Area per Pixel: {}".format(area_perpixel))
    print("    Length per Pixel: {}".format(length_perpixel))

    _, reference_ellipse = fit_ellipse_on_image(reference_image)
    _, target_ellipse = fit_ellipse_on_image(target_image)

    # convert pixel to mm
    reference_ellipse_mm = ((reference_ellipse[0][0] * length_perpixel, reference_ellipse[0][1] * length_perpixel), (reference_ellipse[1][0] * length_perpixel, reference_ellipse[1][1] * length_perpixel), reference_ellipse[2])
    target_ellipse_mm = ((target_ellipse[0][0] * length_perpixel, target_ellipse[0][1] * length_perpixel), (target_ellipse[1][0] * length_perpixel, target_ellipse[1][1] * length_perpixel), target_ellipse[2]) 

    print ("Center Offset in Pixels: {}".format((target_ellipse[0][0] - reference_ellipse[0][0], target_ellipse[0][1] - reference_ellipse[0][1])))

    print (
        "Reference Ellipse: {} x {} at {} x {}".format(
            reference_ellipse_mm[1][0], reference_ellipse_mm[1][1], reference_ellipse_mm[0][0], reference_ellipse_mm[0][1]
        )
    )
    
    print (
        "Target Ellipse: {} x {} at {} x {}".format(
            target_ellipse_mm[1][0], target_ellipse_mm[1][1], target_ellipse_mm[0][0], target_ellipse_mm[0][1]
        )
    )

    print (
        "Center Offset: {}".format(
            (target_ellipse_mm[0][0] - reference_ellipse_mm[0][0], target_ellipse_mm[0][1] - reference_ellipse_mm[0][1])
        )
    )

    # finalize
    cv2.destroyAllWindows()

