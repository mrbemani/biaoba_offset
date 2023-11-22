import cv2
import numpy as np
import math
import sys
import random

def enhance_contrast(img):
    # 将图像转换为灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 应用直方图均衡化
    #enhanced_gray = cv2.equalizeHist(gray)
    _, binary_img = cv2.threshold(gray, 55, 255, cv2.THRESH_BINARY)
     # 生成随机文件名
    #random_filename = f"enhanced_{random.randint(1000, 9999)}.jpg"
    #cv2.imwrite(random_filename, binary_img)


    return binary_img

def calculate_movement(img1, img2, feature_params, lk_params):

    # 确保图片加载成功
    if img1 is None or img2 is None:
        raise ValueError("One or both images could not be loaded. Check the file paths.")
    #裁切标靶位置：
    #x1=2645
    #y1=1045

    #x2=2900
    #y2=1333
    #img1 = img1[y1:y2,x1:x2]
    #img2 = img2[y1:y2,x1:x2]
    # 增强对比度
    #gray1 = enhance_contrast(img1)
    #gray2 = enhance_contrast(img2)
    #gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    #gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    gray1 = img1
    gray2 = img2
    # 在第一张图像上检测特征点
    p0 = cv2.goodFeaturesToTrack(gray1, mask=None, **feature_params)

    # 参数设置用于亚像素角点精化
    subpix_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.001)
    winSize = (15, 15)

    # 对特征点进行亚像素级精化
    cv2.cornerSubPix(gray1, p0, winSize, (-1, -1), subpix_criteria)
    # 使用Lucas-Kanade算法在第二张图像上追踪这些点
    p1, st, err = cv2.calcOpticalFlowPyrLK(gray1, gray2, p0, None, **lk_params)

    # 选取好的追踪点
    good_new = p1[st == 1]
    good_old = p0[st == 1]

    # 计算移动距离
    movement = good_new - good_old
    return movement

def calculate_distance(movement):
    # 计算每个移动向量的欧几里得距离
    distances = np.sqrt((movement[:, 0] ** 2) + (movement[:, 1] ** 2))
    # 计算每个移动向量在 x 轴方向的移动距离
    #distances = np.abs(movement[:, 0])
    return distances

def calculate_trimmed_mean(distances):
    if len(distances) > 2:
        sorted_distances = np.sort(distances)
        trimmed_distances = sorted_distances[1:-1]  # 去掉最小和最大的值
        trimmed_mean = np.mean(trimmed_distances)
        return trimmed_mean
    else:
        # 如果数据点太少，无法去除最大和最小值
        return np.mean(distances)

def perform_compare(img1, img2):
    # 参数设置
    feature_params = dict(maxCorners=200, qualityLevel=0.9, minDistance=3, blockSize=11)
    lk_params = dict(winSize=(35, 35), maxLevel=40, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 1000, 0.0003))

    # 运行光流算法
    movements = calculate_movement(img1, img2, feature_params, lk_params)

    # 计算每个特征点的移动距离
    #distances = calculate_distance(movements)

    # 打印每个特征点的移动距离和计算平均移动距离
    #total_distance = 0
    #for distance in distances:
        #print(f"Feature Point Movement Distance: {distance}")
        #total_distance += distance

    # 计算平均移动距离
    #average_distance = calculate_trimmed_mean(distances)
    average_distance = np.mean(movements, axis=0)
    return average_distance


