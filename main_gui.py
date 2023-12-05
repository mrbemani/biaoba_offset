
import sys
import os
import time
import argparse
import threading
import cv2
import PySimpleGUI as sg
from PIL import Image
from io import BytesIO
import numpy as np
import cam
import avgpixel
import target as tg
import tsutil as tsu

__author__ = 'Mr.Bemani'

mmpp = 2.0  # mm per pixel
PV_W = 512
PV_H = 512
MARKER_DIAMETER = 100.0 # mm
settings = {}  # Global dictionary to store settings

# Modify the font size for text and buttons
button_font = ('Helvetica', 14)  # Example font and size for buttons
text_font = ('Helvetica', 12)    # Example font and size for text


## argparse
parser = argparse.ArgumentParser(description='Marker movement detection.')
parser.add_argument('--camera_idx', type=int, default=0, help='Camera device index')
parser.add_argument('--exposure', type=float, default=5000.0, help='Expose time in (us)')
parser.add_argument('--auto-compare', action='store_true', default=False, help='Perform auto compare')
parser.add_argument('--compare-interval', type=int, default=24, help='Compare interval in hour')
parser.add_argument('--marker', type=str, default="marker.png", help='Marker image')
args = parser.parse_args()

settings['camera_idx'] = args.camera_idx
settings['exposure'] = args.exposure
settings['auto_compare'] = args.auto_compare
settings['compare_interval'] = args.compare_interval
settings['marker'] = args.marker

base_image_array = []
target_image_array = []
marker_rect = (0, 0, 0, 0)
marker_ellipse = None
marker_img = cv2.imread(settings['marker'], 0)

# Add a timer variable at the beginning of your script
next_comparison_time = None

if settings['auto_compare']:
    next_comparison_time = time.time() + settings['compare_interval'] * 3600

# start camera loop
threading.Thread(target=cam.ts_start_camera, args=(settings['camera_idx'], settings['exposure'], cam.MONO12), daemon=True).start()

def convert_to_bytes(image, format='PNG'):
    """ Convert an image to bytes """
    img = Image.fromarray(image)
    with BytesIO() as output_bytes:
        img.save(output_bytes, format=format)
        data = output_bytes.getvalue()
    return data

def perform_manual_comparison(use_mmpp: bool = True):
    global marker_rect, marker_ellipse, mmpp
    # Perform the operation
    img1 = cv2.imread("base_image.bmp", cv2.IMREAD_GRAYSCALE)
    if img1 is None:
        sg.popup('基准图像加载失败')
        return
    if marker_ellipse is None:
        marker_ellipse, marker_rect = tsu.find_marker(img1)
    img2 = cv2.imread("target_image.bmp", cv2.IMREAD_GRAYSCALE)
    if img2 is None:
        sg.popup('目标图像加载失败')
        return
    # (mm per pixel) mmpp = 100.0mm / longest axis of marker ellipse
    mmpp = MARKER_DIAMETER / max(marker_ellipse[1][0], marker_ellipse[1][1])
    img1 = img1[marker_rect[1]:marker_rect[1]+marker_rect[3], marker_rect[0]:marker_rect[0]+marker_rect[2]]
    img2 = img2[marker_rect[1]:marker_rect[1]+marker_rect[3], marker_rect[0]:marker_rect[0]+marker_rect[2]]
    x, y = tg.perform_compare(img1, img2)
    if use_mmpp:
        return x*mmpp, y*mmpp  # Example offset values
    else:
        return x, y, mmpp


def get_image(save_file, nPhoto=20, use_gui: bool = False, loading_window: any = None):
    global previewFrame, marker_ellipse, marker_rect
    cam.nSaveNum = nPhoto
    cam.bSaveBmp = True
    base_image_array.clear()
    while cam.bSaveBmp:
        time.sleep(1)
    for f in cam.savedFiles:
        im = cv2.imread(f, 0)
        base_image_array.append(im)
    fused_base_image = avgpixel.average_image_gray(base_image_array)
    print (fused_base_image.shape)
    if save_file.endswith("base_image.bmp"):
        marker_ellipse, marker_rect = tsu.find_marker(fused_base_image)
    cv2.imwrite(save_file, fused_base_image)
    frm_ = fused_base_image[marker_rect[1]:marker_rect[1]+marker_rect[3],
                            marker_rect[0]:marker_rect[0]+marker_rect[2]]
    cam.clear_saved_files()
    if use_gui:
        previewFrame = cv2.resize(frm_, (PV_W, PV_H))
        window['-IMAGE-'].update(data=convert_to_bytes(previewFrame))
        loading_window.write_event_value('-TASK_DONE-', '')  # Notify the main thread when done
    return marker_ellipse, marker_rect, frm_


def window_apply_op(values):
    settings['auto_compare'] = values['-AUTO_COMPARE-']
    settings['interval'] = int(values['-INTERVAL-'])
    settings['exposure'] = float(values['-EXPOSURE-'])
    cam.set_camera_params(cam.cam, settings['exposure'])
    print('Settings updated:', settings)
    if settings['auto_compare']:
        next_comparison_time = time.time() + settings['compare_interval'] * 3600


def window_reset_op():
    global auto_compare_timer
    settings['auto_compare'] = False
    settings['interval'] = 24
    settings['exposure'] = 5000.0
    window['-AUTO_COMPARE-'].update(settings['auto_compare'])
    window['-INTERVAL-'].update(settings['interval'])
    window['-EXPOSURE-'].update(settings['exposure'])
    cam.set_camera_params(cam.cam, settings['exposure'])
    print('Settings reset:', settings)


def auto_compare_op():
    # Perform manual comparison and update offset display
    if not os.path.exists("base_image.bmp"):
        settings['auto_compare'] = False
        window['-AUTO_COMPARE-'].update(settings['auto_compare'])
        sg.popup('请先获取基准图像')
        return
    # Show a loading pop-up while the task is running
    loading_window = sg.Window('Loading', [[sg.Text('Loading, please wait...')]], modal=True)
    
    threading.Thread(target=get_image, kwargs=dict(save_file="target_image.bmp", nPhoto=20, use_gui=True, loading_window=loading_window), daemon=True).start()
    # Show loading window while the task is running
    while True:
        event, values = loading_window.read(timeout=100)  # Polling interval
        if event in (sg.WIN_CLOSED, '-TASK_DONE-'):
            break

    # Close loading pop-up after the task is done
    loading_window.close()

    x_offset, y_offset = perform_manual_comparison()
    window['-OFFSET-'].update(f'({x_offset}, {y_offset})')


previewFrame = np.zeros((PV_W, PV_H, 1), dtype=np.uint8)  # Black square

# Convert the OpenCV image to bytes
image_bytes = convert_to_bytes(cv2.cvtColor(previewFrame, cv2.COLOR_BGR2RGB))


if __name__ == '__main__':
    # Define the layout for the GUI
    layout = [
        [
            sg.Image(data=image_bytes, key='-IMAGE-'),
            sg.VSeparator(),
            sg.Column([
                [sg.Button('获取基准图像', key='-GET_BASE_IMAGE-', font=button_font)],
                [sg.Button('手动比较', key='-MANUAL_COMPARE-', font=button_font)],
                [sg.HorizontalSeparator()],
                [sg.Checkbox('自动比较', default=settings['auto_compare'], key='-AUTO_COMPARE-', font=text_font)],
                [sg.Text('自动比较间隔 (小时)', font=text_font), sg.InputText(str(settings['compare_interval']), size=(5, 1), key='-INTERVAL-', font=text_font)],
                [sg.HorizontalSeparator()],
                [sg.Text('偏移 (mm):', font=text_font), sg.Text('(x, y)', key='-OFFSET-', font=text_font)],
                [sg.HorizontalSeparator()],
                [sg.Text('曝光 (us)', font=text_font), sg.InputText(str(settings['exposure']), size=(10, 1), key='-EXPOSURE-', font=text_font)],
                [sg.HorizontalSeparator()],
                [sg.Button('应用设置', key='-APPLY-', font=button_font), sg.Button('还原设置', key='-RESET-', font=button_font)]
            ], vertical_alignment='top')
        ]
    ]

    # Create the Window
    window = sg.Window('标靶位移检测', layout)

    # Event Loop
    while True:
        event, values = window.read(timeout=10)
        if event == sg.WIN_CLOSED:
            break

        if event == '-GET_BASE_IMAGE-':
            # Handle Get Base Image button event

            # Show a loading pop-up while the task is running
            loading_window = sg.Window('Loading', [[sg.Text('Loading, please wait...')]], modal=True)
            
            threading.Thread(target=get_image, kwargs=dict(save_file="base_image.bmp", nPhoto=20, use_gui=True, loading_window=loading_window), daemon=True).start()
            # Show loading window while the task is running
            while True:
                event, values = loading_window.read(timeout=100)  # Polling interval
                if event in (sg.WIN_CLOSED, '-TASK_DONE-'):
                    break

            # Close loading pop-up after the task is done
            loading_window.close()


        if settings['auto_compare'] and next_comparison_time is not None:
            if time.time() >= next_comparison_time:
                auto_compare_op()
                next_comparison_time = time.time() + settings['compare_interval'] * 3600


        if event == '-MANUAL_COMPARE-':
            # Perform manual comparison and update offset display
            if not os.path.exists("base_image.bmp"):
                sg.popup('请先获取基准图像')
                continue
            # Show a loading pop-up while the task is running
            loading_window = sg.Window('Loading', [[sg.Text('Loading, please wait...')]], modal=True)
            
            threading.Thread(target=get_image, kwargs=dict(save_file="target_image.bmp", nPhoto=20, use_gui=True, loading_window=loading_window), daemon=True).start()
            # Show loading window while the task is running
            while True:
                event, values = loading_window.read(timeout=100)  # Polling interval
                if event in (sg.WIN_CLOSED, '-TASK_DONE-'):
                    break

            # Close loading pop-up after the task is done
            loading_window.close()

            x_offset, y_offset = perform_manual_comparison()
            window['-OFFSET-'].update(f'({x_offset}, {y_offset})')

        if event == '-APPLY-':
            # Save the settings to the global dictionary
            window_apply_op(values)


        if event == '-RESET-':
            # Reset the settings to the default values
            window_reset_op()

        # Additional event handling logic here if needed

    window.close()
