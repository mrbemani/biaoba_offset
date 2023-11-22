
import math
import cv2
import numpy as np

# create an image template from "marker.png"
# extract features for matching
def create_template(gray: np.ndarray = None):
    if gray is None:
        raise FileNotFoundError("Could not load the marker.png image.")
    
    # create SIFT object
    sift = cv2.SIFT_create(nfeatures=500, nOctaveLayers=5)
    kp, des = sift.detectAndCompute(gray, None)
    img = cv2.drawKeypoints(gray, kp, None, flags=cv2.DRAW_MATCHES_FLAGS_DEFAULT)
    
    # save template image
    cv2.imwrite("template.png", img)
    # save features
    np.save("template.npy", des)
    # return features
    return kp, des, gray

# match features between template and image
def match_template(image: np.ndarray, kp, des, marker_tpl_img: np.ndarray):
    if image is None:
        raise ValueError("Input image is None.")

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # create SIFT object
    sift = cv2.xfeatures2d.SIFT_create(nfeatures=500, nOctaveLayers=5)
    kp2, des2 = sift.detectAndCompute(gray_image, None)
    bf = cv2.FlannBasedMatcher()
    
    # match descriptors
    matches = bf.knnMatch(des, des2, k=2, compactResult=True)
    
    # apply ratio test
    good = []
    for match in matches:
        if len(match) == 2:
            m, n = match
            if m.distance < 0.5 * n.distance:
                good.append([m])
        else:
            print ("bad match:", match)
    
    # draw matches
    img_matches = cv2.drawMatchesKnn(marker_tpl_img, kp, gray_image, kp2, good, None, flags=2)

    # save image
    cv2.imwrite("matches.png", img_matches)

    # return matches
    return good, kp, des, kp2, des2

# load camera intrinsics from cam/iphone13mini_calib.yml
def load_camera_intrinsics():
    fs = cv2.FileStorage("..\\cam\\calib_80mm_x_80mm.yml", cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise FileNotFoundError("Could not open the camera intrinsics file.")

    camera_matrix = fs.getNode("Intrinsics").mat()
    dist_coeffs = fs.getNode("Distortion").mat()
    fs.release()
    
    return camera_matrix, dist_coeffs

if __name__ == '__main__':
    camIntrinsic, distortCoeff = load_camera_intrinsics()
    marker_img = cv2.imread("marker_33.png", 0)
    kp, des, marker_tpl = create_template(marker_img)
    img = cv2.imread("..\\base.bmp")
    if img is None:
        raise FileNotFoundError("Could not load base.bmp.")
    
    # undistort image
    img = cv2.undistort(img, camIntrinsic, distortCoeff)

    good, kp1, des1, kp2, des2 = match_template(img, kp, des, marker_tpl)

    # compute perspective transform use intrinsics
    src_pts = np.float32([kp1[m[0].queryIdx].pt for m in good])#.reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m[0].trainIdx].pt for m in good])#.reshape(-1, 1, 2)
    
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)

    warped_image = cv2.warpPerspective(img, np.linalg.inv(M), (img.shape[1], img.shape[0]))

    cv2.imshow("img", cv2.resize(warped_image, (img.shape[1]//4,img.shape[0]//4)))
    cv2.waitKey(0)

    cv2.destroyAllWindows()

