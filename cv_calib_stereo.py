# -*- coding: utf-8 -*-

__author__ = 'Shi Qi'

import sys
import os
import argparse
import numpy as np
import cv2
from decimal import Decimal


openpose_cam_xml = """<?xml version="1.0"?>
<opencv_storage>
<CameraMatrix type_id="opencv-matrix">
  <rows>3</rows>
  <cols>4</cols>
  <dt>d</dt>
  <data>
    {r11} {r12} {r13} {x} 
    {r21} {r22} {r23} {y} 
    {r31} {r32} {r33} {z}</data></CameraMatrix>
<Intrinsics type_id="opencv-matrix">
  <rows>3</rows>
  <cols>3</cols>
  <dt>d</dt>
  <data>
    {fx} 0. {cx} 0.
    {fy} {cy} 0. 0. 1.</data></Intrinsics>
<Distortion type_id="opencv-matrix">
  <rows>8</rows>
  <cols>1</cols>
  <dt>d</dt>
  <data>
    {k1} {k2}
    {k3} {k4}
    {k5} 0
    0 0</data></Distortion>
</opencv_storage>"""


def deci(n):
    return '%.16e' % Decimal(n)


def get_checkerboard_points(w, h, images, winname="img"):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((h*w,3), np.float32)
    objp[:,:2] = np.mgrid[0:w,0:h].T.reshape(-1,2)
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # camera 2d points in image plane.
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (w,h), None)
        # If found, add object points, image points (after refining them)
        if ret is True:
            objpoints.append(objp)
            corners2=cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners)
            # Draw and display the corners
            cv2.drawChessboardCorners(img, (w,h), corners2, ret)
            ih, iw = gray.shape
            nw = 1280
            nh = int(float(ih) / float(iw) * float(nw))
            ims = cv2.resize(img, (nw, nh))
            cv2.imshow(winname, ims)
            cv2.waitKey(1000)
    cv2.destroyAllWindows()
    return objpoints, imgpoints


def get_stereo_points(w, h, objp, imfileL, imfileR, imw=800):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    imgL = cv2.imread(imfileL)
    imgR = cv2.imread(imfileR)
    print (imfileL, imfileR, w, h)
    grayL = cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    retL, cornersL = cv2.findChessboardCorners(grayL, (w,h), None)
    retR, cornersR = cv2.findChessboardCorners(grayR, (w,h), None)
    # If found, add object points, image points (after refining them)
    if retL is True and retR is True:
        corners2L=cv2.cornerSubPix(grayL, cornersL, (11,11), (-1,-1), criteria)
        corners2R=cv2.cornerSubPix(grayR, cornersR, (11,11), (-1,-1), criteria)
        # Draw and display the corners
        cv2.drawChessboardCorners(imgL, (w,h), corners2L, retL)
        cv2.drawChessboardCorners(imgR, (w,h), corners2R, retR)
        ih, iw = grayL.shape
        nw = imw
        nh = int(float(ih) / float(iw) * float(nw))
        imsL = cv2.resize(imgL, (nw, nh))
        imsR = cv2.resize(imgR, (nw, nh))
        stereoim = np.concatenate((imsL, imsR), axis=1)
        cv2.imshow("Stereo Board View", stereoim)
        return (cornersL, cornersR)
    return None


def calibrate_stereo_camera(cwh, camdir, outdir, kdir, boxsize=1.):
    L_dir = os.path.join(camdir, "L")
    R_dir = os.path.join(camdir, "R")
    w, h = cwh
    L_imgs = []
    R_imgs = []
    if os.path.isdir(L_dir):
        L_imgs = [os.path.join(L_dir, p) for p in os.listdir(L_dir) if p.lower().endswith('.jpg') or p.lower().endswith('.png')]
    else:
        print ("[ERROR] L-dir does not exist!")
        return 1
    if os.path.isdir(R_dir):
        R_imgs = [os.path.join(R_dir, p) for p in os.listdir(R_dir) if p.lower().endswith('.jpg') or p.lower().endswith('.png')]
    else:
        print ("[ERROR] R-dir does not exist!")
        return 1
    if len(L_imgs) != len(R_imgs):
        print ("[ERROR] Stereo Images must be equal number.")
        return 2
    if len(L_imgs) < 2:
        print ("[ERROR] Stereo Images are empty.")
        return 3
    L_kXML = os.path.join(kdir, "L.xml")
    R_kXML = os.path.join(kdir, "R.xml") 
    L_camXML = os.path.join(outdir, "L.xml")
    R_camXML = os.path.join(outdir, "R.xml")
    imh, imw = cv2.imread(L_imgs[0]).shape[:2]
    imsize = (imw, imh)
    L_imgpoints = []
    R_imgpoints = []
    objpoints = []
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((h*w,3), np.float32)
    objp[:,:2] = np.mgrid[0:w,0:h].T.reshape(-1,2)
    objp *= boxsize
    for idx in range(len(L_imgs)):
        r = get_stereo_points(w, h, objp, L_imgs[idx], R_imgs[idx], 800)
        if r is not None:
            L_imp, R_imp = r
            objpoints.append(objp)
            L_imgpoints.append(L_imp)
            R_imgpoints.append(R_imp)
        k = cv2.waitKey(50)
        if k == 27:
            print ("Esc pressed. Quit.")
            return 0
    camMatrixL = np.zeros((3, 3), np.float32)
    camDistL = np.zeros(5, dtype=np.float32)
    camMatrixR = np.zeros((3, 3), np.float32)
    camDistR = np.zeros(5, dtype=np.float32)
    camMatrixL[0,0] = 1.0
    camMatrixL[1,1] = 1.0
    camMatrixR[0,0] = 1.0
    camMatrixR[1,1] = 1.0
    retL, rvecsL, tvecsL = 0., None, None
    flags = 0
    if not os.path.isfile(L_kXML) or not os.path.isfile(R_kXML):
        print ("Mono calibration for L and R separately...")
        retL, camMatrixL, camDistL, rvecsL, tvecsL = cv2.calibrateCamera(objpoints, L_imgpoints, imsize, camMatrixL, camDistL, flags=0)
        retR, camMatrixR, camDistR, rvecsR, tvecsR = cv2.calibrateCamera(objpoints, R_imgpoints, imsize, camMatrixR, camDistR, flags=0)
        print ("Done.")
    else:
        print ("Loading precalibrated files for L and R...")
        cv_file_L = cv2.FileStorage(L_kXML, cv2.FILE_STORAGE_READ)
        cv_file_R = cv2.FileStorage(R_kXML, cv2.FILE_STORAGE_READ)
        camMatrixL = cv_file_L.getNode("Intrinsics").mat()
        camDistL = cv_file_L.getNode("Distortion").mat()
        cv_file_L.release()
        camMatrixR = cv_file_R.getNode("Intrinsics").mat()
        camDistR = cv_file_R.getNode("Distortion").mat()
        cv_file_R.release()
        print ("Done.")
    R = np.eye(3, dtype=np.float32)
    T = np.zeros((3, 1), dtype=np.float32)
    flags = cv2.CALIB_FIX_INTRINSIC
    stereocalib_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)
    retval, camMatrixL, camDistL, camMatrixR, camDistR, R, T, E, F = cv2.stereoCalibrate(
        objpoints, 
        L_imgpoints, R_imgpoints, 
        camMatrixL, camDistL, camMatrixR, camDistR, 
        imsize, R, T, criteria=stereocalib_criteria, flags=flags)
    
    print ("===")
    print ("retval: {}".format(retval))
    print ("camMatrixL: {}".format(camMatrixL))
    print ("camDistL: {}".format(camDistL))
    print ("camMatrixR: {}".format(camMatrixR))
    print ("camDistR: {}".format(camDistR))
    print ("R: {}".format(R))
    print ("T: {}".format(T))
    print ("E: {}".format(E))
    print ("F: {}".format(F))
    print ("===")
    if outdir is not None:
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        print ("Saving...")
        with open(L_camXML, "w+") as fp:
            print ("writing L to L.xml")
            t = openpose_cam_xml.format(
                fx=deci(camMatrixL[0][0]), fy=deci(camMatrixL[1][1]), cx=deci(camMatrixL[0][2]), cy=deci(camMatrixL[1][2]), 
                k1=deci(camDistL[0][0]), k2=deci(camDistL[1][0]), k3=deci(camDistL[2][0]), k4=deci(camDistL[3][0]), k5=deci(camDistL[4][0]), 
                r11=1., r12=0., r13=0., x=0.,
                r21=0., r22=1., r23=0., y=0.,
                r31=0., r32=0., r33=1., z=0.
            )
            fp.write(t)
            fp.flush()
        with open(R_camXML, "w+") as fp:
            print ("writing R to R.xml")
            t = openpose_cam_xml.format(
                fx=deci(camMatrixR[0][0]), fy=deci(camMatrixR[1][1]), cx=deci(camMatrixR[0][2]), cy=deci(camMatrixR[1][2]), 
                k1=deci(camDistR[0][0]), k2=deci(camDistR[1][0]), k3=deci(camDistR[2][0]), k4=deci(camDistR[3][0]), k5=deci(camDistR[4][0]), 
                r11=deci(R[0][0]), r12=deci(R[0][1]), r13=deci(R[0][2]), x=deci(T[0][0]),
                r21=deci(R[1][0]), r22=deci(R[1][1]), r23=deci(R[1][2]), y=deci(T[1][0]),
                r31=deci(R[2][0]), r32=deci(R[2][1]), r33=deci(R[2][2]), z=deci(T[2][0])
            )
            fp.write(t)
            fp.flush()   
        print ("Done saving.")         
    return 0


def main(args):
    if type(args) is not argparse.Namespace:
        print ("[ERROR] Invalid Command-line parameters!")
        return 1

    if args.checkerboard is None or len(args.checkerboard) != 2:
        print ("[ERROR] Invalid --checkerboard. Should be in the form: WxH")
        return 2
    ret = 0
    checkerboardWH = args.checkerboard

    ret = calibrate_stereo_camera(checkerboardWH, os.path.abspath(args.camera_dir), os.path.abspath(args.output_params_dir), os.path.abspath(args.cameras_param_dir), args.boxwidth)

    return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stereo-Camera Calibration.')
    parser.add_argument('-b', '--checkerboard', type=lambda s: [int(x) for x in s.split('x')], help="checkerboard resolution. in the form: WxH")
    parser.add_argument('-w', '--boxwidth', type=float, help="unit box size on the checkerboard in (mm). default: 1.0", default=1.0)
    parser.add_argument('-k', '--cameras_param_dir', type=str, help="L and R camera Intrinsic and Distortion opencv-XMLs.")
    parser.add_argument('-c', '--camera_dir', type=str, help="camera image directory. it should contain L and R subdir themselves contain JPEGs.")
    parser.add_argument('-o', '--output_params_dir', type=str, help="output directory to store camera parameters.")
    args = parser.parse_args()
    print ("\n=== Start ===\n")
    ret = main(args)
    if ret == 0:
        print ("\n=== Done ===\n")
    else:
        print ("\n[ERROR] Program ended unexpectedly! Errno: {}\n".format(ret))
        print ("\n=== Failed ===\n")


