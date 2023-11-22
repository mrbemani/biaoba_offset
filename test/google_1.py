import cv2
import numpy as np

# Convert corner points to cv2.KeyPoint objects
def convertToKeyPoints(corners):
    return [cv2.KeyPoint(x=pt[0][0], y=pt[0][1], size=1) for pt in corners]

# Your existing function
def findCornersSubpix(gray, winSize, zeroZone, criteria):
    corners = cv2.goodFeaturesToTrack(gray, 33, 0.01, 10)
    corners = cv2.cornerSubPix(gray, corners, winSize, zeroZone, criteria)
    return corners

# Additional functions for feature matching and finding homography
def match_features(image1, image2):
    # Convert images to grayscale
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Detect corners in both images
    corners1 = findCornersSubpix(gray1, (5,5), (-1,-1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
    corners2 = findCornersSubpix(gray2, (5,5), (-1,-1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))

     # Convert corners to KeyPoints
    keypoints1 = convertToKeyPoints(corners1)
    keypoints2 = convertToKeyPoints(corners2)

    # Feature descriptor
    sift = cv2.SIFT_create()

    # Find descriptors based on KeyPoint objects
    keypoints1, descriptors1 = sift.compute(gray1, keypoints1)
    keypoints2, descriptors2 = sift.compute(gray2, keypoints2)

    # Matcher - FLANN or BFMatcher
    matcher = cv2.BFMatcher()
    matches = matcher.knnMatch(descriptors1, descriptors2, k=2)

    # Filter matches using the Lowe's ratio test
    good_matches = []
    for m,n in matches:
        if m.distance < 0.75*n.distance:
            good_matches.append(m)

    # Extract location of good matches
    points1 = np.float32([keypoints1[m.queryIdx].pt for m in good_matches])
    points2 = np.float32([keypoints2[m.trainIdx].pt for m in good_matches])

    # Find homography
    H, status = cv2.findHomography(points1, points2, cv2.RANSAC, 5.0)

    return H

# Usage example
image1 = cv2.imread('marker_33.png')
image2 = cv2.imread('..\\test_input_1.png')

homography_matrix = match_features(image1, image2)

# Warp source image to destination based on homography
im_out = cv2.warpPerspective(image1, homography_matrix, (image2.shape[1],image2.shape[0]))

# Display images
cv2.imshow("Source Image", cv2.resize(image1, (image1.shape[1]//6), image1.shape[0]//6))
cv2.imshow("Destination Image", cv2.resize(image2, (image2.shape[1]//6, image2.shape[0]//6)))
cv2.imshow("Warped Source Image", im_out)

cv2.waitKey(0)
