import pyaudio
import time
import base64
from PyQt5.QtCore import QThread, pyqtSignal


class AudioStreamThread(QThread):
    """ 在独立线程中运行音频捕获并发送流 """
    audio_sent = pyqtSignal(str)  # 用于向主线程发送音频流

    def __init__(self, ws, parent=None):
        super().__init__(parent)
        self.ws = ws
        self.audio_enabled = False
        self.p = pyaudio.PyAudio()
        self.stream = None

    def toggle_audio(self, audio_enabled):
        """ 切换音频状态 """
        self.audio_enabled = audio_enabled
        if self.audio_enabled and self.stream is None:
            # 开启音频流时初始化麦克风
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        elif not self.audio_enabled and self.stream is not None:
            # 关闭音频流时释放麦克风
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def run(self):
        """ 音频流的捕获与发送 """
        while True:
            if self.audio_enabled and self.stream is not None:
                try:
                    # 从麦克风捕获音频数据
                    audio_data = self.stream.read(1024)  # 捕获1024个样本

                    # 将音频数据编码为base64字符串
                    audio_as_text = "audio:" + base64.b64encode(audio_data).decode('utf-8')

                    # 发送音频数据到服务器
                    self.ws.send(audio_as_text)
                    self.audio_sent.emit(audio_as_text)  # 发射信号，通知主线程

                    time.sleep(0.0001)  # 控制发送音频数据的间隔

                except Exception as e:
                    print(f"Error capturing audio: {e}")
                    break
            else:
                time.sleep(0.1)  # 如果音频没有开启，稍作休眠
