
import sys
import os

os_type = sys.platform
import threading

if os_type == 'win32':
    import msvcrt
else:
    import termios
    import tty

import cv2
import numpy as np
import time



from ctypes import *
if os_type == 'linux':
    libc = cdll.LoadLibrary("libc.so.6")
elif os_type == 'darwin':
    libc = cdll.LoadLibrary("libc.dylib")

MvImport = "C:\\Program Files (x86)\\MVS\\Development\\Samples\\Python\\MvImport" #"./MvImport_win"
if os_type == 'linux':
    MvImport = "./MvImport_linux"
elif os_type == 'darwin':
    MvImport = "/Library/MVS_SDK/Samples/Python/MvImport"

sys.path.append(MvImport)
from MvCameraControl_class import *

g_bExit = False
g_currentFrame = None
g_rclock = threading.Lock()

# get system temp directory
TMP_DIR = "./tmp/" #os.environ.get('TEMP') or "./tmp/"
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

cam = 0

MONO8 = 17301505
MONO12 = 17825797

bSaveBmp = False
nSaveNum = 0
savedFiles = []

# 为线程定义一个函数
def work_thread(cam=0):
    global bSaveBmp, nSaveNum
    stOutFrame = MV_FRAME_OUT()
    memset(byref(stOutFrame), 0, sizeof(stOutFrame))
    while True:
        #print("start capture ...", end='')
        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
        #print("ok")
        if None != stOutFrame.pBufAddr and 0 == ret:
            # get cv2 image
            #print ("get one frame: Width[%d], Height[%d], enPixelType[0x%x]"  % (stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.enPixelType))
            frame_len = stOutFrame.stFrameInfo.nFrameLen
            buf_image = None
            if bSaveBmp is True:
                if len(savedFiles) >= nSaveNum:
                    bSaveBmp = False
                    print ("All Image Saved")
                print ("Saving ... ")
                if len(savedFiles) >= nSaveNum:
                    bSaveBmp = False
                    print ("save image number enough!")
                if stOutFrame.stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                    buf_image = (c_ubyte * frame_len)()
                elif stOutFrame.stFrameInfo.enPixelType == PixelType_Gvsp_Mono12:
                    buf_image = (c_uint16 * frame_len)()
                g_rclock.acquire()
                if os_type == 'win32':
                    cdll.msvcrt.memcpy(byref(buf_image), stOutFrame.pBufAddr, frame_len)
                else:
                    libc.memcpy(byref(buf_image), stOutFrame.pBufAddr, frame_len)
                Save_Bmp(cam, buf_image, stOutFrame.stFrameInfo, False)
                if len(savedFiles) > 0:
                    print (savedFiles[-1])
                g_rclock.release()
            nRet = cam.MV_CC_FreeImageBuffer(stOutFrame)
            if buf_image is not None:
                if os_type == 'win32':
                    del buf_image
                else:
                    libc.free(buf_image)
        else:
            print ("no data[0x%x]" % ret)
        if g_bExit == True:
            break


def clear_saved_files():
    if len(savedFiles) > 0:
        for f in savedFiles:
            os.remove(f)
        savedFiles.clear()

def getCurrentFrame():
    global g_currentFrame
    frame = None
    g_rclock.acquire()
    if g_currentFrame is not None:
        frame = g_currentFrame.copy()
    g_rclock.release()
    return frame


def get_camera_list(return_json=False):
    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE
    
    # ch:枚举设备 | en:Enum device
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print ("enum devices fail! ret[0x%x]" % ret)
        return None, False, -1

    if deviceList.nDeviceNum == 0:
        print ("find no device!")
        return None, False, 0

    print ("Find %d devices!" % deviceList.nDeviceNum)

    camera_info_list = []
    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        print ("\ngige device: [%d]" % i)
        strModeName = ""
        for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
            if per == 0:
                break
            strModeName = strModeName + chr(per)
        print ("device model name: %s" % strModeName)

        serial_number = ""
        for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chSerialNumber:
            if per == 0:
                break
            serial_number = serial_number + chr(per)
        print ("serial number: %s" % serial_number)

        nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
        nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
        nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
        nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
        cam_info = dict(
            idx = i,
            id = serial_number,
            name = strModeName,
            ip = f"{nip1}.{nip2}.{nip3}.{nip4}",
        )
        print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        camera_info_list.append(cam_info)
    
    if return_json:
        return camera_info_list, True, deviceList.nDeviceNum
    else:
        return deviceList, True, deviceList.nDeviceNum


def init_camera(deviceList: any, cameraIdx: int, exposureTime: float = 2000.0, pixelFormat: int = PixelType_Gvsp_Mono12):
    nConnectionNum = cameraIdx # found camera index

    if int(nConnectionNum) >= deviceList.nDeviceNum:
        print ("intput error!")
        return None, -1

    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()

    # ch:选择设备并创建句柄 | en:Select device and create handle
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents
    
    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print ("create handle fail! ret[0x%x]" % ret)
        return None, ret
    
    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print ("open device fail! ret[0x%x]" % ret)
        return None, ret
    
    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
            if ret != 0:
                print ("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print ("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

    stBool = c_bool(False)
    ret =cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
    if ret != 0:
        print ("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)
    else:
        print ("AcquisitionFrameRateEnable: %d" % stBool.value)
    
    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print ("set trigger mode fail! ret[0x%x]" % ret)
        return ret

    ret = cam.MV_CC_SetEnumValue("PixelFormat", pixelFormat) #0x01100005
    if ret != 0:
        print ("set PixelFormat fail! ret[0x%x]" % ret)
        return ret

    return cam


def set_camera_params(cam: any, exposureTime: float = 2000.0, gain: float = -9999.0):
    ret = cam.MV_CC_SetEnumValue("ExposureAuto", 0)
    time.sleep(0.2)
    ret = cam.MV_CC_SetFloatValue("ExposureTime", exposureTime)
    if ret != 0:
        print ("set ExposureTime fail! ret[0x%x]" % ret)
        return ret

    if gain > -9999.0:
        ret = cam.MV_CC_SetFloatValue("Gain", float(gain))
        if ret != 0:
            print("set Gain fail! ret[0x%x]" % ret)
            return ret

    return 0

def set_camera_exposure(cam: any, exposureTime: float):
    ret = cam.MV_CC_SetEnumValue("ExposureAuto", 0)
    time.sleep(0.2)
    ret = cam.MV_CC_SetFloatValue("ExposureTime", exposureTime)
    if ret != 0:
        print ("set ExposureTime fail! ret[0x%x]" % ret)
        return ret
    return 0

def set_camera_gain(cam: any, gain: float):
    ret = cam.MV_CC_SetFloatValue("Gain", float(gain))
    if ret != 0:
        print("set Gain fail! ret[0x%x]" % ret)
        return ret
    return 0

def start_camera(cam: any, autoGrab: bool = True):
    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print ("start grabbing fail! ret[0x%x]" % ret)
        return ret
    
    hThreadHandle = None
    if autoGrab:
        try:
            hThreadHandle = threading.Thread(target=work_thread, args=(cam,), daemon=True)
            hThreadHandle.start()
        except:
            print ("error: unable to start thread")
    
    return hThreadHandle


def stop_camera(cam: any, cam_thread: threading.Thread):
    global g_bExit
    g_bExit = True
    time.sleep(0.5)
    cam_thread.join(1.0)

    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print ("stop grabbing fail! ret[0x%x]" % ret)
        return ret
    
    return 0


def close_camera(cam: any):
    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print ("close deivce fail! ret[0x%x]" % ret)
        return ret
    
    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print ("destroy handle fail! ret[0x%x]" % ret)
        return ret
    
    return 0


# 存BMP图像
def Save_Bmp(cam, buf_save_image, st_frame_info, bLock=True):

    if 0 == buf_save_image:
        return

    # 获取缓存锁
    if bLock is True:
        g_rclock.acquire()

    file_path = os.path.join(TMP_DIR, str(st_frame_info.nFrameNum) + ".bmp")
    c_file_path = file_path.encode('ascii')

    stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
    stSaveParam.enPixelType = st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
    stSaveParam.nWidth = st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
    stSaveParam.nHeight = st_frame_info.nHeight  # ch:相机对应的高 | en:Height
    stSaveParam.nDataLen = st_frame_info.nFrameLen
    stSaveParam.pData = cast(buf_save_image, POINTER(c_ubyte))
    stSaveParam.enImageType = MV_Image_Bmp  # ch:需要保存的图像类型 | en:Image format to save
    stSaveParam.nQuality = 9
    stSaveParam.pcImagePath = create_string_buffer(c_file_path)
    stSaveParam.iMethodValue = 2
    ret = cam.MV_CC_SaveImageToFileEx(stSaveParam)

    savedFiles.append(file_path)

    if bLock is True:
        g_rclock.release()

    return ret


def ts_start_camera(camera_idx:int = 0, exposure_time: float = 2000.0, gain: float = 0.0, pixelFormat: int = PixelType_Gvsp_Mono12):
    global g_currentFrame, g_bExit, cam

    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
    
    # ch:枚举设备 | en:Enum device
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print ("enum devices fail! ret[0x%x]" % ret)
        sys.exit()

    if deviceList.nDeviceNum == 0:
        print ("find no device!")
        sys.exit()

    print ("Find %d devices!" % deviceList.nDeviceNum)

    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        print ("\ngige device: [%d]" % i)
        strModeName = ""
        for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
            if per == 0:
                break
            strModeName = strModeName + chr(per)
        print ("device model name: %s" % strModeName)

        nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
        nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
        nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
        nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
        print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        
    nConnectionNum = camera_idx # found camera index

    if int(nConnectionNum) >= deviceList.nDeviceNum:
        print ("intput error!")
        sys.exit()

    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()
    
    # ch:选择设备并创建句柄 | en:Select device and create handle
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print ("create handle fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print ("open device fail! ret[0x%x]" % ret)
        sys.exit()
    
    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
            if ret != 0:
                print ("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print ("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

    stBool = c_bool(False)
    ret =cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
    if ret != 0:
        print ("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)

    # ch:设置触发模式为off | en:Set trigger mode as off
    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print ("set trigger mode fail! ret[0x%x]" % ret)
        sys.exit()

    
    ret = cam.MV_CC_SetEnumValue("PixelFormat", pixelFormat) #0x01100005
    if ret != 0:
        print ("set PixelFormat fail! ret[0x%x]" % ret)
        sys.exit()
    
    ret = cam.MV_CC_SetEnumValue("ExposureAuto", 0)
    time.sleep(0.2)
    ret = cam.MV_CC_SetFloatValue("ExposureTime", exposure_time)
    if ret != 0:
        print ("set ExposureTime fail! ret[0x%x]" % ret)
        sys.exit()
    
    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print ("start grabbing fail! ret[0x%x]" % ret)
        sys.exit()

    try:
        hThreadHandle = threading.Thread(target=work_thread, args=(cam,))
        hThreadHandle.start()
    except:
        print ("error: unable to start thread")
        
    while g_bExit == False:
        time.sleep(0.01)

    g_bExit = True
    hThreadHandle.join()

    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print ("stop grabbing fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print ("close deivce fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print ("destroy handle fail! ret[0x%x]" % ret)
        sys.exit()


if __name__ == "__main__":
    # test case
    threading.Thread(target=ts_start_camera, args=(0, 2000000.0), daemon=True).start()
    frame = None
    while True:
        _frm = getCurrentFrame()
        if _frm is not None:
            frame = _frm.copy()
        if frame is not None:
            img_scaled = cv2.normalize(frame, dst=None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)
            cv2.imshow("frame", img_scaled)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            g_bExit = True
            time.sleep(0.5)
            break
    cv2.destroyAllWindows()
    sys.exit()