import cv2
import threading
import queue
from typing import Union, List
import numpy as np
from .BaseVideoCapture import BaseVideoCapture


class FasterVideoCapture(BaseVideoCapture):
    VIDEO_END_FLAG = -1

    def __init__(
        self,
        videoPath: Union[List[str], str],
        initStep: int = 0,
        mtx: Union[None, np.array] = None,
        dist: Union[None, np.array] = None,
        interval: int = 1,
        buffer_size: int = 5,
    ) -> None:
        super().__init__(
            videoPath=videoPath,
            initStep=initStep,
            mtx=mtx,
            dist=dist,
            interval=interval,
        )
        self.interval = interval
        self.buffer_size = buffer_size
        self._read_count = initStep
        self.frame_buffer = queue.Queue(maxsize=buffer_size)
        self.stop_event = threading.Event()
        self.read_thread = threading.Thread(target=self._preload_frames, daemon=True)
        self.read_thread.start()

    def _preload_frames(self):
        while not self.stop_event.is_set():
            ret, frame = super().read()
            if ret:
                self.frame_buffer.put((self._capture_count, frame, self._capture_count_video), block=True)
            else:
                self.frame_buffer.put(
                    (FasterVideoCapture.VIDEO_END_FLAG, None, self._capture_count_video), block=True
                )

    def read(self):
        count, frame, frameCount = self.frame_buffer.get(block=True)
        if count == FasterVideoCapture.VIDEO_END_FLAG:
            return False, None
        self._read_count += self.interval
        self._frameCount = frameCount
        assert count == self._read_count
        return True, frame

    def release(self):
        self.stop_event.set()
        self.read_thread.join()
        self.cap.release()

    def count(self):
        return self._read_count

    def getVideoFrameCount(self):
        return self._frameCount