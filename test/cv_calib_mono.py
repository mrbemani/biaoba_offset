# -*- coding: utf-8 -*-

__author__ = 'Shi Qi'

import sys
import os
import argparse
import json
import numpy as np
import cv2
from decimal import Decimal





def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def deci(n):
    return '%.16e' % Decimal(n)


def get_checkerboard_points(w, h, objp, images, imw=5472, winname="Camera Checkerboard View"):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # camera 2d points in image plane.
    for fname in images:
        img = cv2.imread(fname)
        print (f"processing {fname} ...")
        ih, iw = img.shape[:2]
        nw = imw
        nh = int(float(ih) / float(iw) * float(nw))
        img = cv2.resize(img, (nw, nh))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, (w,h), None)
        # If found, add object points, image points (after refining them)
        if ret is True:
            objpoints.append(objp)
            corners2=cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            ims = cv2.drawChessboardCorners(img, (w,h), corners2, ret)
            imgpoints.append(corners)
            ih, iw = ims.shape[:2]
            nw = 1280
            nh = int(float(ih) / float(iw) * float(nw))
            ims = cv2.resize(ims, (nw, nh))
            # Draw and display the corners
            cv2.imshow(winname, ims)
            k = cv2.waitKey(100)
            if k == 27:
                break
    return objpoints, imgpoints


def calibrate_mono_camera(cwh, cb_unit_size, camdir, outfile):
    w, h = cwh
    imgs = []
    if os.path.isdir(camdir):
        imgs = [os.path.join(camdir, p) for p in os.listdir(camdir) if p.lower().endswith('.jpg') or p.lower().endswith('.png') or p.lower().endswith('.bmp')]
    else:
        print ("[ERROR] camdir does not exist!")
        return (1, None)
    if len(imgs) < 2:
        print ("[ERROR] Images are empty.")
        return (2, None)
    imh, imw = cv2.imread(imgs[0]).shape[:2]
    imsize = (imw, imh)
    imgpoints = []
    objpoints = []
    objp = np.zeros((h*w,3), np.float32)
    objp[:,:2] = np.mgrid[0:w,0:h].T.reshape(-1,2) * cb_unit_size
    r = get_checkerboard_points(w, h, objp, imgs, imw)
    if r is not None:
        objpoints, imgpoints = r
    else:
        return (3, None)
    # camMatrix = np.zeros((3, 3), np.float32)
    # camMatrix[0,0] = 1.0
    # camMatrix[1,1] = 1.0
    camMatrix = cv2.initCameraMatrix2D(objpoints, imgpoints, imsize)
    print ("initial camMatrix: \n{}".format(camMatrix))
    camDist = np.zeros(8, dtype=np.float32)
    retval, camMatrix, camDist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, imsize, camMatrix, camDist, flags=0)
    #retval, camMatrix, camDist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, imsize, camMatrix, camDist, flags=flags)

    print ("===")
    print ("retval: {}".format(retval))
    print ("Intrinsics: {}".format(camMatrix))
    print ("Distortion: {}".format(camDist))
    print ("===")
    if outfile is not None:
        print ("Saving...")
        cv_file = cv2.FileStorage(outfile, cv2.FILE_STORAGE_WRITE)
        #cv_file.write("retval", retval)
        cv_file.write("Intrinsics", camMatrix)
        cv_file.write("Distortion", camDist)
        cv_file.release()
        print ("Done saving.")         
    return (0, (retval, camMatrix, camDist, rvecs, tvecs))


def undistort_image(i_im, o_im, k, d):
    im = cv2.imread(i_im)
    ih, iw = im.shape[:2]
    # newk, roi = cv2.getOptimalNewCameraMatrix(k, d, (ih, iw), 1, (ih, iw))
    # print (newk)
    # print (roi)
    # crop the image
    # x, y, w, h = roi
    # undistort
    dst = cv2.undistort(im, k, d, None, k)
    #dst = dst[y:y+h, x:x+w]
    cv2.imwrite(o_im, dst)


def main(args):
    if type(args) is not argparse.Namespace:
        print ("[ERROR] Invalid Command-line parameters!")
        return 1

    ret = 0
    
    if args.mode == "calib":
        if args.checkerboard is None or len(args.checkerboard) != 2:
            print ("[ERROR] Invalid --checkerboard. Should be in the form: WxH")
            return 2
        
        checkerboardWH = args.checkerboard
        cam_input_dir = os.path.abspath(args.camera_dir)
        cam_out_dir = os.path.abspath(args.output_params_dir)
        if not os.path.isdir(cam_input_dir):
            print ("Error: {} does not exist!".format(args.camera_dir))
            return 1
        if not os.path.isdir(cam_out_dir):
            os.mkdir(cam_out_dir)
        camdirs = [x for x in os.listdir(cam_input_dir) if os.path.isdir(os.path.join(cam_input_dir, x))]
        totalcams = len(camdirs)
        donecams = 0
        cb_unit_size = args.checkerboard_unit or 1
        cams = []
        for camdir in camdirs:
            print ("[{} / {}] Calibrating: {} ...".format(donecams+1, totalcams, camdir))
            r, cam = calibrate_mono_camera(checkerboardWH, cb_unit_size, os.path.join(cam_input_dir, camdir), os.path.join(cam_out_dir, "{}.yml".format(camdir)))
            if r != 0:
                print ("Failed: {}".format(camdir))
            else:
                donecams += 1
                cams.append(cam)
        print ("\nCameras calibrated: {} in {}.\n".format(donecams, totalcams))
    elif args.mode == "undistort":
        imgdir = os.path.abspath(args.images_dir)
        unddir = os.path.abspath(args.undistorted_dir)
        camfile = os.path.abspath(args.input_camera_params_file)
        k = None
        d = None
        if not os.path.isfile(camfile):
            print ("Error: input camera parameters file is invalid.")
            return 1
        else:
            k_file = cv2.FileStorage(camfile, cv2.FILE_STORAGE_READ)
            k = k_file.getNode("Intrinsics").mat()
            d = k_file.getNode("Distortion").mat()
        if not os.path.isdir(imgdir):
            print ("Error: input images_dir is invalid.")
            return 2
        if not os.path.isdir(unddir):
            os.mkdir(unddir)
        imgs = [p for p in os.listdir(imgdir) if p.lower().endswith('.jpg') or p.lower().endswith('.png') or p.lower().endswith('.bmp')]
        total_img = len(imgs)
        if total_img < 1:
            print("No Image for undistorting.")
            return 3
        und_img = 0
        for im in imgs:
            opimg = os.path.join(imgdir, im)
            print ("[{} / {}] Undistorting Image: {} ...".format(und_img+1, total_img, opimg))
            undistort_image(opimg, os.path.join(unddir, im), k, d)
            und_img += 1
        print ("\nDone!\nImages undistorted: {} in {}.\n".format(und_img, total_img))
    else:
        print ("Error: Invalid --mode. only calib and undistort are implemented.")
        return 2
    return ret

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monno-Camera Calibration.')
    parser.add_argument('-b', '--checkerboard', type=lambda s: [int(x) for x in s.split('x')], help="checkerboard resolution. in the form: WxH")
    parser.add_argument('-c', '--camera_dir', type=str, help="camera image directory. it should contain camera subdirs which themselves contain JPEGs, BMPs or PNGs.")
    parser.add_argument('-o', '--output_params_dir', type=str, help="output directory to store camera parameters.")
    parser.add_argument('-m', '--mode', type=str, default="calib", help="script mode, calib | undistort. default: calib")
    parser.add_argument('-k', '--input_camera_params_file', type=str, help="only for undistort. path to camera parameters YAML file.")
    parser.add_argument('-i', '--images_dir', type=str, help="only for undistort. input images to undistort", )
    parser.add_argument('-u', '--undistorted_dir', type=str, help="only for undistort. output undistorted images", default="undistorted")
    parser.add_argument('-s', '--checkerboard_unit', type=int, help="checkerboard unit size in mm.", default=1)
    args = parser.parse_args()
    print ("\n=== Start ===\n")
    ret = main(args)
    if ret == 0:
        print ("\n=== Done ===\n")
    else:
        print ("\n[ERROR] Program ended unexpectedly! Errno: {}\n".format(ret))
        print ("\n=== Failed ===\n")
    cv2.destroyAllWindows()


