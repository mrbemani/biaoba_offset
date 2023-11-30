# record random noise data of x, y movement

import time
import main_gui as mg

# create a mockup_win object that has a member function write_event_value
mockup_win = type('mockup_win', (object,), {'write_event_value': lambda self, a, b: print (a, b)})()

offsets = []

if __name__ == '__main__':
    mg.get_image(mockup_win, "base_image.bmp", 20)
    time.sleep(15*60)
    try:
        while True:
            mg.get_image(mockup_win, "target_image.bmp", 20)
            dx, dy, mmpp = mg.perform_manual_comparison(use_mmpp=False)
            ts = time.time()
            offsets.append((ts, dx, dy))
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            print (time_str, dx, dy)
            with open("offsets.csv", "a") as f:
                f.write(f"{time_str},{dx},{dy},{mmpp}\r\n")
            time.sleep(15*60)
    except KeyboardInterrupt:
        print ("KeyboardInterrupt")
    
    print ("done!")

