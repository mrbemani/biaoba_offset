from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.tpl.html')

@app.route('/images/<path:path>')
def send_image(path):
    return send_from_directory('images', path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)


@app.route('/camera-calibration', methods=['GET'])
def camera_calibration():
    camera_id = request.args.get('camera_id')
    return render_template('camera_calibration.tpl.html', camera_id=camera_id)


@app.route('/save-camera-calibration', methods=['POST'])
def save_camera_calibration():
    calibration_data = request.json
    # Save calibration data to a file or process as needed
    return jsonify({"success": True})


@app.route('/draw-boxes', methods=['GET'])
def draw_boxes():
    camera_id = request.args.get('camera_id')
    # Draw boxes on image
    return render_template('drawbox.tpl.html', camera_id=camera_id, image_url='https://www.w3schools.com/w3css/img_lights.jpg')

@app.route('/save-boxes', methods=['POST'])
def save_boxes():
    box_data = request.json
    # Save box data to a file or process as needed
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
