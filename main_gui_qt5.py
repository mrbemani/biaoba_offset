# main gui use pyqt5

__author__ = 'Mr.Bemani'

import sys
import os
import time
import dotenv
from PyQt5.QtWidgets import QProgressDialog, QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QCheckBox, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import cv2
import numpy as np
import cam

PV_W = 800
PV_H = 600

# load .env
dotenv.load_dotenv()

camera_idx = os.environ.get('BB_CAMERA_IDX') or 0
exposure = os.environ.get('BB_EXPOSURE') or 2000.0
auto_compare = os.environ.get('BB_AUTO_COMPARE') or False
compare_interval = os.environ.get('BB_COMPARE_INTERVAL') or 24


class ImageWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("Marker Tracking")

        # Global settings dictionary
        self.settings = {}

        # Initialize OpenCV image (replace with actual image)
        self.previewFrame = np.zeros((PV_H, PV_W), dtype=np.uint8)
        self.base_image = None
        self.target_image = None

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()

        # Image label
        self.image_label = QLabel()
        self.main_layout.addWidget(self.image_label)

        # Right sidebar layout
        self.sidebar_layout = QVBoxLayout()

        # Add sidebar widgets
        self.get_image_button = QPushButton("获取基准图像")
        self.manual_compare_button = QPushButton("手动比较")
        self.auto_compare_checkbox = QCheckBox("自动比较")
        self.compare_interval_input = QLineEdit(str(compare_interval))
        self.result_label_xy = QLabel("偏移:")
        self.result_label_xy_value = QLabel("(x, y)")
        self.exposure_input = QLineEdit(str(exposure))
        self.apply_button = QPushButton("应用设置")

        # Connect buttons to functions
        self.get_image_button.clicked.connect(self.get_base_image)
        self.manual_compare_button.clicked.connect(self.manual_compare)
        self.apply_button.clicked.connect(self.apply_settings)

        # Spacer item to push everything to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.sidebar_layout.addItem(spacer)

        # Add widgets to sidebar layout
        self.sidebar_layout.addWidget(self.get_image_button)
        self.sidebar_layout.addWidget(self.manual_compare_button)
        self.sidebar_layout.addWidget(self.auto_compare_checkbox)
        self.sidebar_layout.addWidget(self.result_label_xy)
        self.sidebar_layout.addWidget(self.result_label_xy_value)
        self.sidebar_layout.addWidget(QLabel("自动对比间隔 (小时)"))
        self.sidebar_layout.addWidget(self.compare_interval_input)
        self.sidebar_layout.addWidget(QLabel("曝光 (微秒)"))
        self.sidebar_layout.addWidget(self.exposure_input)
        self.sidebar_layout.addWidget(self.apply_button)

        # Wrapper layout for sidebar
        sidebar_wrapper_layout = QVBoxLayout()
        sidebar_wrapper_layout.addLayout(self.sidebar_layout)

        # Add sidebar wrapper layout to main layout
        self.main_layout.addLayout(sidebar_wrapper_layout)

        # Set the main layout
        self.central_widget.setLayout(self.main_layout)

        # Update the image
        self.update_image()

    def update_image(self):
        # Convert the 16-bit mono image to QImage
        height, width = self.previewFrame.shape
        bytes_per_line = width  # 1 bytes per pixel
        
        # Create QImage from the scaled image
        q_img = QImage(self.previewFrame.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

        # Convert QImage to QPixmap and display it
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)

    def get_base_image(self):
        # Function to handle 'Get Base Image' button click
        print("Get Base Image button clicked")
        
        # Create a QProgressDialog
        progress_dialog = QProgressDialog("Processing...", "Abort", 0, 0, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)  # Show immediately
        progress_dialog.setCancelButton(None)  # Remove the cancel button
        progress_dialog.show()

        QApplication.processEvents()  # Process any pending events to update the UI

        time.sleep(3)
        # Perform the operation
        self.base_image = cam.getCurrentFrame()
        if self.base_image is not None:
            img_scaled = np.clip(self.base_image / 16, 0, 255).astype(np.uint8)
            frm_ = cv2.resize(img_scaled, (800, 600))
            self.previewFrame = frm_
            self.update_image()

        # Close the progress dialog
        progress_dialog.close()

    def manual_compare(self):
        # Function to handle 'Manual Compare' button click
        print("Manual Compare button clicked")

    def apply_settings(self):
        # Function to handle 'Apply' button click
        # Save settings to the global dictionary
        self.settings['auto_compare'] = self.auto_compare_checkbox.isChecked()
        self.settings['compare_interval'] = self.compare_interval_input.text()
        self.settings['exposure'] = self.exposure_input.text()
        print("Settings applied:", self.settings)

if __name__ == "__main__":
    import argparse
    import threading
    parser = argparse.ArgumentParser(description='Marker movement detection.')
    parser.add_argument('--camera_idx', type=int, default=0, help='Camera device index')
    parser.add_argument('--exposure', type=float, default=2000.0, help='Expose time in (us)')
    parser.add_argument('--auto-compare', type=bool, default=False, help='Auto compare')
    parser.add_argument('--compare-interval', type=int, default=24, help='Compare interval in hour')
    args = parser.parse_args()

    camera_idx = args.camera_idx
    exposure = args.exposure
    auto_compare = args.auto_compare
    compare_interval = args.compare_interval


    #deviceList, ret, num = cam.get_camera_list()
    #if ret != True:
    #    print("No cameras found!")
    #    sys.exit(1)
    #if deviceList.nDeviceNum == 0:
    #    print("No cameras found!")
    #    sys.exit(1)
    #camera = cam.init_camera(deviceList, camera_idx, exposure)
    #if not camera:
    #    print("Failed to initialize camera!")
    #    sys.exit(1)
    # test case
    threading.Thread(target=cam.ts_start_camera, args=(camera_idx, exposure, cam.MONO12), daemon=True).start()
    app = QApplication(sys.argv)
    mainWin = ImageWindow()
    mainWin.show()
    #cam.stop_camera(camera, cam_thread)
    #cam.close_camera(camera)
    sys.exit(app.exec_())
