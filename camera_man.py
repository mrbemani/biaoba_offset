# camera manager


from typings import Tuple
import tsmarker


class TSCamera:
    def __init__(self, camera_idx: int = 0, exposure: float = 150.0, markers: Tuple[tsmarker.TSMarker]):
        self.camera_idx = camera_idx if camera_idx >= 0 else 0
        self.exposure = exposure if exposure > 0 else 150.0
        self.markers = markers

    def add_marker(self, marker: tsmarker.TSMarker):
        self.markers.append(marker)

    def add_marker(self, marker_id: int, marker_name: str, marker_roi: tuple = None):
        self.markers.append(tsmarker.TSMarker(marker_id, marker_name, marker_roi))

    def remove_marker(self, marker_id: int):
        for i, marker in enumerate(self.markers):
            if marker.marker_id == marker_id:
                self.markers.pop(i)
                return True
        return False

    def remove_marker(self, marker_name: str):
        for i, marker in enumerate(self.markers):
            if marker.marker_name == marker_name:
                self.markers.pop(i)
                return True
        return False


class TSCameraManager:
    def __init__(self):
        self.cameras = dict()

    def add_camera(self, camera: TSCamera):
        self.cameras[camera.camera_idx] = camera

    def add_camera(self, camera_idx: int = 0, exposure: float = 150.0, markers: Tuple[tsmarker.TSMarker] = None):
        self.cameras[camera_idx] = TSCamera(camera_idx, exposure, markers)

    def remove_camera(self, camera_idx: int):
        if camera_idx in self.cameras:
            self.cameras.pop(camera_idx)
            return True
        return False

    def get_camera(self, camera_idx: int):
        if camera_idx in self.cameras:
            return self.cameras[camera_idx]
        return None

    def get_marker(self, camera_idx: int, marker_id: int):
        if camera_idx in self.cameras:
            return self.cameras[camera_idx].markers[marker_id]
        return None

    def get_marker(self, marker_uri: str):
        camera_idx, marker_id = marker_uri.split(':')
        camera_idx = int(camera_idx)
        marker_id = int(marker_id)
        if camera_idx in self.cameras:
            return self.cameras[camera_idx].markers[marker_id]

    def get_markers(self, camera_idx: int):
        if camera_idx in self.cameras:
            return self.cameras[camera_idx].markers
        return None

