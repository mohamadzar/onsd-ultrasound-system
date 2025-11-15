import cv2
import numpy as np

class OpenCVCamera:
    def __init__(self, device_index: int = 0, width: int = 1280, height: int = 720):
        self.cap = cv2.VideoCapture(device_index)
        if width and height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

    def read(self) -> np.ndarray | None:
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self) -> None:
        if self.cap:
            self.cap.release()