
import atexit
import cv2
import numpy as np

frame_idx = 1

cap = cv2.VideoCapture(1, apiPreference=cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 25)

cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
cv2.resizeWindow("frame", 1280, 720)
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        cv2.imshow('frame', frame)
        k = cv2.waitKey(1)
        if k == ord('q'):
            break
        elif k == ord('s'):
            cv2.imwrite(f'logi_calib_{frame_idx}.png', frame)
            print('frame saved')
            frame_idx += 1
except KeyboardInterrupt as kbi:
    print("KeyboardInterrupt")
finally:
    cap.release()

# on sys.exit
# cv2.destroyAllWindows()
# cap.release()
def onExit():
    cv2.destroyAllWindows()
    if cap != None:
        cap.release()

atexit.register(onExit)

