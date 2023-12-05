# record random noise data of x, y movement

import os
import time
import main_gui as mg
import matplotlib.pyplot as plt
import cv2

offsets = []
current_plot = None

# plot current offset
def plot_offsets(offset_list):
    global current_plot
    start_ts = offset_list[0][0]
    ts = [o[0]-start_ts for o in offset_list]
    dx = [o[1] for o in offset_list]
    dy = [o[2] for o in offset_list]
    mmpp = [o[3] for o in offset_list]
    # plot dx in red, dy in blue, mmpp in light-gray
    # new plot
    plt.figure()
    plt.plot(ts, dx, 'r', label='dx')
    plt.plot(ts, dy, 'b', label='dy')
    plt.plot(ts, mmpp, 'xkcd:light gray', label='mmpp')
    plt.legend()
    # nonblock show plot
    # plt.pause(0.001)
    # save
    date_str = time.strftime("%Y_%m_%d", time.localtime(time.time()))
    current_plot = f"records/offsets_{date_str}.png"
    plt.savefig(current_plot)
    plt.close()
    return current_plot

if __name__ == '__main__':
    elp, roi, _ = mg.get_image("base_image.bmp", 20, use_gui=False)
    cv2.namedWindow("base")
    cv2.namedWindow("target")
    cv2.namedWindow("plot")
    cv2.moveWindow("base", 100, 100)
    cv2.moveWindow("target", 350, 100)
    cv2.moveWindow("plot", 600, 100)
    if not os.path.exists("records"):
        os.makedirs("records")
    time.sleep(mg.args.compare_interval)
    today_at_0000_timestamp = int(time.time()) - (int(time.time()) % (24*60*60))
    base_roi_img = cv2.imread("base_image.bmp")[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
    try:
        while True:
            #time.sleep(mg.args.compare_interval)
            now = int(time.time())
            date_str = time.strftime("%Y_%m_%d", time.localtime(now))
            if now > today_at_0000_timestamp + 24*60*60:
                # new day, reset
                today_at_0000_timestamp = now - (now % (24*60*60))
                mg.get_image("base_image.bmp", 20, use_gui=False)
                base_roi_img = cv2.imread("base_image.bmp")[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
                cv2.imwrite(f"base_roi_{date_str}.bmp", base_roi_img)
                offsets = []
                continue
            mg.get_image("target_image.bmp", 20, use_gui=False)
            dx, dy, mmpp = mg.perform_manual_comparison(use_mmpp=False)
            ts = time.time()
            offsets.append((ts, dx, dy, mmpp))
            time_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(ts))
            date_str = time.strftime("%Y_%m_%d", time.localtime(ts))
            plot_img = plot_offsets(offsets)
            with open(f"records/offsets_{date_str}.csv", "a", encoding="utf-8") as f:
                f.write(f"{time_str},{dx},{dy},{mmpp}\r\n")
            # show result
            target_roi_img = cv2.imread("target_image.bmp")[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
            cv2.imwrite(f"target_roi_{time_str}.bmp", target_roi_img)
            cv2.imshow("base", cv2.resize(base_roi_img, (224, 224)))
            cv2.imshow("target", cv2.resize(target_roi_img, (224, 224)))
            cv2.imshow("plot", cv2.imread(plot_img))
            k = cv2.waitKey(mg.args.compare_interval*1000)
            if k == 27: # esc
                break
    except KeyboardInterrupt:
        print ("KeyboardInterrupt")
    finally:
        cv2.destroyAllWindows()
    print ("done!")

