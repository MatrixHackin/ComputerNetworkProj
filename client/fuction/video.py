import cv2
import time
import base64
from PyQt5.QtCore import QThread, pyqtSignal


class VideoStreamThread(QThread):
    """ 在独立线程中运行视频捕获并发送流 """
    frame_sent = pyqtSignal(str)  # 用于向主线程发送视频帧

    def __init__(self, ws, parent=None):
        super().__init__(parent)
        self.ws = ws
        self.capture = None
        self.video_enabled = False

    def toggle_video(self, video_enabled):
        """ 切换视频状态 """
        self.video_enabled = video_enabled
        if self.video_enabled and self.capture is None:
            # 开启视频流时初始化摄像头
            self.capture = cv2.VideoCapture(1)

            while True:
                ret, frame = self.capture.read()
                if not ret:
                    print("摄像头无法打开！")
                    break
                cv2.imshow("Capture", frame)

            if not self.capture.isOpened():
                print("Error: Could not open video camera.")
                self.video_enabled = False  # 摄像头打开失败
                return
        elif not self.video_enabled and self.capture is not None:
            # 关闭视频流时释放摄像头
            self.capture.release()
            self.capture = None

    def run(self):
        """ 视频流的捕获与发送 """
        while True:
            if self.video_enabled and self.capture is not None:
                ret, frame = self.capture.read()
                if not ret:
                    print("Error: Failed to capture image.")
                    break
                # 转为JPEG格式
                _, buffer = cv2.imencode('.jpg', frame)
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')

                # 发送视频帧到服务器
                self.ws.send(jpg_as_text)
                self.frame_sent.emit(jpg_as_text)  # 发射信号，通知主线程
                time.sleep(0.1)  # 控制发送帧的间隔
            else:
                time.sleep(0.1)  # 如果视频没有开启，稍作休眠
