

import threading
import cv2
import numpy as np
import cam
import cv2.aruco as aruco

# Initialize the video capture
threading.Thread(target=cam.ts_start_camera, args=(0,), daemon=True).start()


# Define the dictionary and parameters for ArUco marker detection
# 5x5 in size
# each cell is 5cm x 5cm
# 1 for white cell, 0 for black cell
# 0 0 0 0 0
# 0 0 1 1 0
# 0 1 0 1 0
# 0 0 0 1 0
# 0 0 0 0 0
byteList = np.array([[0, 0, 0, 0, 0],[0, 0, 1, 1, 0],[0, 1, 0, 1, 0],[0, 0, 0, 1, 0],[0, 0, 0, 0, 0]], dtype=np.uint8)
aruco_dict = aruco.Dictionary(byteList, _markerSize=5, maxcorr=1)
parameters = aruco.DetectorParameters()

# Camera calibration parameters (replace with your camera's parameters)
camera_matrix = np.array([
   [2.0732592956367906e+04, 0., 2.7537088954443120e+03],
   [0., 2.0688824190191150e+04, 2.2924074326704267e+03],
   [0., 0., 1.]
], dtype=np.float64)

dist_coeffs = np.array([
   -3.1061568292327224e-01, 
   3.8916871254822745e+01,
   5.0771971557899490e-03, 
   -1.9050305893242422e-03,
   -1.1620912124203378e+03 
], dtype=np.float64)

def draw_cube(img, corners, imgpts):
    imgpts = np.int32(imgpts).reshape(-1,2)

    # Draw ground floor in green
    img = cv2.drawContours(img, [imgpts[:4]], -1, (255,), -3)

    # Draw pillars in blue
    for i, j in zip(range(4), range(4, 8)):
        img = cv2.line(img, tuple(imgpts[i]), tuple(imgpts[j]), (255,), 3)

    # Draw top layer in red
    img = cv2.drawContours(img, [imgpts[4:]], -1, (255,), 3)

    return img

while True:
    _frm = cam.getCurrentFrame()
    if _frm is None:
        continue

    # Convert frame to grayscale
    frame = _frm.copy()
    gray = frame
    
    # Detect ArUco markers
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        # Estimate pose of each marker
        rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, 0.05, camera_matrix, dist_coeffs)

        for i in range(len(ids)):
            # Draw axis for each marker
            aruco.drawAxis(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], 0.03)

            # Define the cube points in 3D space
            cube_points = np.float32([[0, 0, 0], [0, 0.05, 0], [0.05, 0.05, 0], [0.05, 0, 0],
                                      [0, 0, -0.05],[0, 0.05, -0.05],[0.05, 0.05, -0.05],[0.05, 0, -0.05]])

            # Project 3D points to image plane
            imgpts, jac = cv2.projectPoints(cube_points, rvecs[i], tvecs[i], camera_matrix, dist_coeffs)

            # Draw the cube
            frame = draw_cube(frame, corners[i], imgpts)
    
    # Display the frame
    cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
