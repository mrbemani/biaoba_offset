import cv2
import PySimpleGUI as sg
import json

def resize_image(image, max_size=(1200, 900)):
    h, w = image.shape[:2]
    scale = min(max_size[0] / w, max_size[1] / h)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h)), scale

def draw_boxes(window, image, scale):
    boxes = []
    drawing = False  # True if drawing a new box
    moving = False   # True if moving an existing box
    ix, iy = -1, -1  # Initial x, y coordinates
    current_box = -1  # Index of the selected box

    def draw_rectangle_with_drag(event, x, y, flags, param):
        nonlocal ix, iy, drawing, moving, current_box
        x, y = int(x / scale), int(y / scale)  # Adjust coordinates based on scale

        # Check if a box is selected
        def box_selected(x, y, box):
            x1, y1, x2, y2, _ = box
            return x1 < x < x2 and y1 < y < y2

        if event == cv2.EVENT_LBUTTONDOWN:
            selected_box = [i for i, box in enumerate(boxes) if box_selected(x, y, box)]
            if selected_box:
                current_box = selected_box[0]
                moving = True
                ix, iy = x, y
            elif not drawing:
                drawing = True
                ix, iy = x, y
                current_box = len(boxes)
                boxes.append((ix, iy, x, y, ''))

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                boxes[current_box] = (ix, iy, x, y, boxes[current_box][4])
            elif moving and current_box != -1:
                dx, dy = x - ix, y - iy
                ix, iy = x, y
                x1, y1, x2, y2, name = boxes[current_box]
                boxes[current_box] = (x1 + dx, y1 + dy, x2 + dx, y2 + dy, name)

        elif event == cv2.EVENT_LBUTTONUP:
            if drawing:
                drawing = False
                boxes[current_box] = (ix, iy, x, y, boxes[current_box][4])
            if moving:
                moving = False
                # Do not update the box size here, just end the moving process

    cv2.namedWindow('Image')
    cv2.setMouseCallback('Image', draw_rectangle_with_drag)

    while True:
        temp_image = image.copy()
        for i, box in enumerate(boxes):
            color = (255, 0, 0) if i == current_box else (0, 255, 0)  # Blue for selected, Green for others
            cv2.rectangle(temp_image, (int(box[0] * scale), int(box[1] * scale)), 
                          (int(box[2] * scale), int(box[3] * scale)), color, 2)

        cv2.imshow('Image', temp_image)

        k = cv2.waitKey(1) & 0xFF
        
        if k == 27:
            break
        elif k == ord('d') and current_box != -1:
            boxes.pop(current_box)
            current_box = -1
        elif k == ord('n') and current_box != -1:
            name = sg.popup_get_text('Enter name for the box', 'Box Name')
            if name:
                boxes[current_box] = (*boxes[current_box][:4], name)

    cv2.destroyAllWindows()
    return [(int(x1/scale), int(y1/scale), int(x2/scale), int(y2/scale), name) for (x1, y1, x2, y2, name) in boxes]

# GUI Layout with a right sidebar for buttons
image_viewer_column = [
    [sg.Image(key='-IMAGE-')]
]

button_column = [
    [sg.Button('Load Image')],
    [sg.Button('Draw Boxes')],
    [sg.Button('Save Boxes')],
    [sg.Button('Exit')]
]

layout = [
    [sg.Column(image_viewer_column),
     sg.VSeperator(),
     sg.Column(button_column, element_justification='center')]
]

window = sg.Window('Box Drawer', layout)

while True:
    event, values = window.read()
    if event in (None, 'Exit'):
        break
    elif event == 'Load Image':
        filename = sg.popup_get_file('Load Image', no_window=True)
        if filename:
            image = cv2.imread(filename)
            resized_image, scale = resize_image(image)
            window['-IMAGE-'].update(data=cv2.imencode('.png', resized_image)[1].tobytes())
    elif event == 'Draw Boxes':
        if 'image' in locals():
            boxes = draw_boxes(window, image, scale)
    elif event == 'Save Boxes':
        if 'boxes' in locals():
            with open('boxes.json', 'w') as f:
                json.dump(boxes, f)

window.close()
