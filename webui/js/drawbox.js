document.addEventListener("DOMContentLoaded", function () {
    var canvas = new fabric.Canvas('imageCanvas', {
        width: 1280,
        height: 720
    });

    var isDrawing = false;
    var rect, isDown, origX, origY;
    var modeToggleButton = document.getElementById('modeToggle');
    var deleteBoxButton = document.getElementById('deleteBox');
    var saveBoxesButton = document.getElementById('saveBoxes');
    var cancelBoxesButton = document.getElementById('cancelBoxes');

    document.getElementById('imageLoader').addEventListener('change', function (e) {
        var file = e.target.files[0];
        var reader = new FileReader();
        reader.onload = function (f) {
            fabric.Image.fromURL(f.target.result, function (img) {
                // Calculate the scaling factor to maintain aspect ratio
                var canvasAspectRatio = canvas.width / canvas.height;
                var imgAspectRatio = img.width / img.height;
                var scaleFactor;
    
                if (canvasAspectRatio > imgAspectRatio) {
                    // Canvas is wider than image
                    scaleFactor = canvas.height / img.height;
                } else {
                    // Canvas is narrower than image
                    scaleFactor = canvas.width / img.width;
                }
    
                img.set({
                    angle: 0,
                    padding: 0,
                    cornersize: 0,
                    selectable: false,  // Make the image unselectable
                });
                img.scale(scaleFactor);  // Scale the image to fit the canvas
    
                canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas));
            });
        };
        reader.readAsDataURL(file);
    });    

    document.getElementById('modeToggle').onclick = function () {
        isDrawing = !isDrawing;
        
        if (isDrawing) {
            modeToggleButton.textContent = '画框模式';
            modeToggleButton.classList.add('is-warning');
        } else {
            modeToggleButton.textContent = '选择模式';
            modeToggleButton.classList.remove('is-warning');
        }

        canvas.selection = !isDrawing;  // Toggle selection based on the drawing mode
    };

    canvas.on('selection:created', function(e) {
        console.log("selection:created");
        if (e.target && e.target.type === 'rect') {
            document.getElementById('attributeForm').style.display = 'block';
            document.getElementById('markerName').value = e.target.name || '';
            document.getElementById('markerDiameter').value = e.target.diameter || '';
            deleteBoxButton.removeAttribute('disabled');
        }
    });

    canvas.on('selection:updated', function(e) {
        console.log("selection:updated");
        if (e.target && e.target.type === 'rect') {
            document.getElementById('attributeForm').style.display = 'block';
            document.getElementById('markerName').value = e.target.name || '';
            document.getElementById('markerDiameter').value = e.target.diameter || '';
            deleteBoxButton.removeAttribute('disabled');
        }
    });
    
    canvas.on('selection:cleared', function() {
        console.log("selection:cleared");
        document.getElementById('attributeForm').style.display = 'none';
        deleteBoxButton.setAttribute('disabled', true);
    }); 
    
    canvas.on('mouse:down', function (o) {
        if (!isDrawing || canvas.getActiveObject()) return;
        isDown = true;
        var pointer = canvas.getPointer(o.e);
        origX = pointer.x;
        origY = pointer.y;
        rect = new fabric.Rect({
            left: origX,
            top: origY,
            width: 1,
            height: 1,
            stroke: 'red',
            strokeWidth: 2,
            strokeUniform: true,  // Keep the stroke width consistent when resizing
            fill: 'transparent',
            transparentCorners: false,
            hasBorders: true,
            lockScalingX: false,
            lockScalingY: false,
            lockRotation: true,
            hasControls: true,
            hasRotatingPoint: false
        });
        canvas.add(rect);
    });

    canvas.on('mouse:move', function (o) {
        if (!isDown || !isDrawing) return;
        var pointer = canvas.getPointer(o.e);
        if(origX > pointer.x){
            rect.set({ left: Math.abs(pointer.x) });
        }
        if(origY > pointer.y){
            rect.set({ top: Math.abs(pointer.y) });
        }
        rect.set({ width: Math.abs(origX - pointer.x) });
        rect.set({ height: Math.abs(origY - pointer.y) });
        canvas.renderAll();
    });

    canvas.on('mouse:up', function () {
        isDown = false;
    });

    document.getElementById('deleteBox').onclick = function () {
        var activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'rect') {
            canvas.remove(activeObject);
            canvas.discardActiveObject(); // Discard the selection after deletion
            canvas.requestRenderAll(); // Re-render the canvas
        }
    };

    document.getElementById('saveAttributes').addEventListener('click', function() {
        var activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'rect') {
            activeObject.name = document.getElementById('markerName').value;
            activeObject.diameter = document.getElementById('markerDiameter').value;
            document.getElementById('attributeForm').style.display = 'none';
            canvas.discardActiveObject();
            canvas.requestRenderAll();
        }
    });

    saveBoxesButton.onclick = function () {
        // save box data to a json file
        var activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.type === 'rect') {
            var boxData = {
                name: activeObject.name,
                diameter: activeObject.diameter,
                x: activeObject.left,
                y: activeObject.top,
                width: activeObject.width,
                height: activeObject.height
            };
            console.log(boxData);
            var data = JSON.stringify(boxData);
            var blob = new Blob([data], {type: "text/plain;charset=utf-8"});
            saveAs(blob, "box.json");
        }
        else {
            alert("请先选择一个框");
        }
    };

    cancelBoxesButton.onclick = function () {
        // Add logic to cancel box data
    }
});
