import base64
import sys
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QImage
import pyaudio
from client.fuction.video import VideoStreamThread
from client.fuction.audio import AudioStreamThread
import cv2
import websocket
import websockets
from client.config import *
import asyncio
import requests
import threading
import numpy as np
from PIL import Image
import io


class MeetingWindow(QWidget):
    # 定义一个信号来更新 UI
    message_received = pyqtSignal(str)

    def __init__(self, conference_id, user_id):
        super().__init__()
        self.conference_id = conference_id
        self.user_id = user_id
        # self.conference_id=1
        # self.user_id=1

        self.setWindowTitle(f"Meeting Room {conference_id}")
        self.setWindowIcon(QIcon("client/ui/resources/icon.png"))
        self.setFixedSize(1920, 1080)  # Full screen

        # 状态管理
        self.audio_enabled = False  # 默认为闭麦
        self.video_enabled = False  # 默认为关闭摄像头
        self.speaker_view = False  # 默认为等分模式
        self.view_toggle_count = 0  # 视图切换计数器
        self.audio_toggle_count = 0  # 点击计数器
        self.video_toggle_count = 0  # 点击计数器
        self.websocket = None

        self.capture = None  # 摄像头捕获对象
        self.video_thread = None
        self.audio_thread = None
        self.user_video_label = QLabel()  # 当前用户视频的显示区域
        self.timer = QTimer()
        self.video_dict = dict()  # {user_id: show_label_id}
        self.audio_output = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=44100, output=True,
                                                   frames_per_buffer=1024)

        self.initUI()
        self.timer.timeout.connect(self.update_camera_frame)  # 定时器更新摄像头画面
        self.timer.start(100)  # 每100毫秒（0.1秒）更新一次画面
        self.video_msg_ws = None
        self.audio_ws = None
        self.connect()

    def initUI(self):
        main_layout = QHBoxLayout()

        # Left Sidebar with Audio and Video buttons
        left_sidebar_widget = self.create_left_sidebar()  # Create left sidebar widget
        left_sidebar_widget.setFixedWidth(int(self.width() * 0.074))

        # Chat area (right side)
        chat_area = self.create_right_sidebar_chatting()
        chat_area.setFixedWidth(int(self.width() * 0.3))

        # Video area (centered in the window)
        video_area = self.create_video_area()
        video_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 自适应大小

        # Main Layout
        main_layout.addWidget(left_sidebar_widget)  # Add the widget, not just the layout
        main_layout.addWidget(video_area)
        main_layout.addWidget(chat_area)  # Use addWidget instead of addLayout

        self.setLayout(main_layout)

    def connect(self):
        url1 = f"ws://{SERVER_IP}:{MAIN_SERVER_PORT}/ws/{self.conference_id}/{self.user_id}/video_msg"
        url2 = f"ws://{SERVER_IP}:{MAIN_SERVER_PORT}/ws/{self.conference_id}/{self.user_id}/audio"
        self.video_msg_ws = websocket.create_connection(url1)
        self.audio_ws = websocket.create_connection(url2)
        # 创建视频流线程
        self.video_thread = VideoStreamThread(self.video_msg_ws)
        self.video_thread.start()
        # 创建音频流线程
        self.audio_thread = AudioStreamThread(self.audio_ws)
        self.audio_thread.start()
        # 启动后台线程来监听服务器消息
        listen_thread1 = threading.Thread(target=self.listen_for_video_msg)
        listen_thread1.daemon = True  # 后台线程，当主线程结束时自动结束
        listen_thread1.start()
        listen_thread2 = threading.Thread(target=self.listen_for_audio)
        listen_thread2.daemon = True  # 后台线程，当主线程结束时自动结束
        listen_thread2.start()

    def create_left_sidebar(self):
        sidebar_layout = QVBoxLayout()

        # Audio Button with icon (圆形按钮)
        self.audio_button = QPushButton()
        self.audio_icon_off = QIcon("client/ui/resources/audio_off_icon.png")  # 静音图标
        self.audio_icon_on = QIcon("client/ui/resources/audio_on_icon.png")  # 开启麦克风图标
        self.audio_button.setIcon(self.audio_icon_off)  # 默认静音
        self.audio_button.setIconSize(QSize(40, 40))  # 设置图标大小
        self.audio_button.clicked.connect(self.toggle_audio)

        # Video Button with icon (圆角方形按钮)
        self.video_button = QPushButton()
        self.video_icon_off = QIcon("client/ui/resources/video_off_icon.png")  # 关闭摄像头图标
        self.video_icon_on = QIcon("client/ui/resources/video_on_icon.png")  # 开启摄像头图标
        self.video_button.setIcon(self.video_icon_off)  # 默认关闭摄像头
        self.video_button.setIconSize(QSize(40, 40))  # 设置图标大小
        self.video_button.clicked.connect(self.toggle_video)

        # Create the "Exit Meeting" button
        self.exit_button = QPushButton()  # 设置按钮文本
        self.exit_button.setIcon(QIcon("client/ui/resources/exit_icon.png"))  # 退出会议图标
        self.exit_button.setIconSize(QSize(40, 40))  # 设置图标大小
        self.exit_button.clicked.connect(self.exit_meeting)  # 点击事件处理函数

        # Create the "Close Meeting" button
        self.close_button = QPushButton()  # 设置按钮文本
        self.close_button.setIcon(QIcon("client/ui/resources/close_icon.png"))  # 关闭会议图标
        self.close_button.setIconSize(QSize(40, 40))  # 设置图标大小
        self.close_button.clicked.connect(self.end_meeting)  # 点击事件处理函数

        # 切换模式按钮
        self.switch_mode_button = QPushButton()
        self.switch_mode_button.setIcon(QIcon("client/ui/resources/switch_icon.png"))
        self.switch_mode_button.setIconSize(QSize(40, 40))
        self.switch_mode_button.setToolTip("切换演讲者视图模式")
        self.switch_mode_button.clicked.connect(self.toggle_view_mode)

        # Add buttons to the sidebar layout
        sidebar_layout.addWidget(self.exit_button)
        sidebar_layout.addWidget(self.audio_button)
        sidebar_layout.addWidget(self.video_button)
        sidebar_layout.addWidget(self.close_button)
        sidebar_layout.addWidget(self.switch_mode_button)
        sidebar_layout.addStretch()

        # Create a QWidget to hold the layout
        sidebar_widget = QWidget()  # Wrap the layout inside a QWidget
        sidebar_widget.setLayout(sidebar_layout)  # Set layout to the widget

        # 样式设置
        sidebar_widget.setStyleSheet("""
            QPushButton {
                background-color: #f6f8fa; /* GitHub 风格的浅灰背景 */
                border: 1px solid #d0d7de; /* 边框颜色 */
                border-radius: 8px; /* 圆角 */
                padding: 10px; /* 内边距 */
            }
            QPushButton:hover {
                background-color: #e1e4e8; /* 悬停时背景变暗 */
            }
            QPushButton:pressed {
                background-color: #d7dce1; /* 点击时背景更暗 */
            }
            QPushButton:focus {
                outline: none; /* 去掉按钮聚焦时的外框 */
            }
            QPushButton::icon {
                margin: 0; /* 确保图标居中对齐 */
            }
        """)

        return sidebar_widget  # Return the widget

    def create_right_sidebar_chatting(self):
        """ 创建固定的聊天面板 """
        # 主布局
        main_layout = QVBoxLayout()

        # 对话列表（QListWidget 自带滚动功能）
        self.chat_list = QListWidget()
        self.chat_list.setFixedHeight(900)
        self.chat_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)  # 平滑滚动
        self.chat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 隐藏水平滚动条
        main_layout.addWidget(self.chat_list)

        # 底部布局（输入框和按钮）
        input_container = QWidget()
        input_layout = QVBoxLayout()

        # 输入框
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("请输入消息...")
        self.text_input.setFixedHeight(100)  # 固定高度
        input_layout.addWidget(self.text_input)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignRight)

        # 上传文件按钮
        self.upload_button = QPushButton()
        self.upload_button.setIcon(QIcon("client/ui/resources/add_icon.png"))
        self.upload_button.setToolTip("上传文件")
        self.upload_button.setFixedSize(40, 40)
        self.upload_button.clicked.connect(self.upload_file)
        button_layout.addWidget(self.upload_button)

        # 发送按钮
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon("client/ui/resources/send_icon.png"))
        self.send_button.setToolTip("发送消息")
        self.send_button.setFixedSize(40, 40)
        self.send_button.clicked.connect(self.send_message)
        button_layout.addWidget(self.send_button)

        # 将按钮布局添加到底部布局
        input_layout.addLayout(button_layout)
        input_container.setLayout(input_layout)
        main_layout.addWidget(input_container)

        # 设置主界面中的聊天部分
        chat_widget = QWidget()
        chat_widget.setLayout(main_layout)

        # 样式设置
        chat_widget.setStyleSheet("""
            QWidget {
                background-color: #f6f8fa; 
                border: 1px solid #d0d7de; 
                border-radius: 6px; 
            }
        """)
        self.chat_list.setFixedHeight(700)
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff; /* 白色背景 */
                border: none; /* 无边框 */
                padding: 10px; /* 内边距 */
                font-size: 18px;
                color: #24292e; /* 深灰色字体 */
            }
            QListWidget::item {
                margin: 5px 0; /* 项目之间的间距 */
                padding: 10px;
                background-color: #f6f8fa; /* 条目背景 */
                border: 1px solid #d0d7de;
                border-radius: 4px;
                white-space: normal; /* 启用换行 */
                word-wrap: break-word; /* 允许长单词换行 */
            }
        """)
        self.text_input.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                padding: 10px;
                font-size: 20px;
                color: #24292e;
                font-family: Arial, sans-serif;
                font-weight: bold;
            }
            QTextEdit:focus {
                border-color: #0366d6; /* 聚焦时的边框颜色 */
            }
        """)
        self.upload_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #d0d7de;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c8c8c8; /* Hover 效果 */
            }
        """)
        self.send_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #1a7f37;
                color: #ffffff;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c8c8c8; /* Hover 效果 */
            }
        """)

        return chat_widget

    def send_message(self):
        """ 发送消息到对话框 """
        message = self.text_input.toPlainText()
        time = datetime.now()
        if message:
            self.chat_list.addItem(f"你: [{time}] {message}")
            self.video_msg_ws.send(f"broadcast:[{time}] {message}")
            self.text_input.clear()

    def listen_for_video_msg(self):
        """ 在后台线程中监听 WebSocket 消息 """
        while True:
            try:
                message = self.video_msg_ws.recv()  # 接收来自服务器的消息
                if message:
                    print("receive a message")
                    if message.startswith("msg:"):
                        print("receive a msg")
                        self.chat_list.addItem(message[len("msg:"):])
                    elif message.startswith("video:"):
                        datas = message.split(":")
                        user_id = datas[1]
                        print(f"user_id = {user_id}")
                        data = datas[2]
                        print(f"receive a video from {user_id}")
                        show_id = -1
                        if user_id in self.video_dict.keys():
                            show_id = self.video_dict[user_id]
                        else:
                            show_id = len(self.video_dict) + 1
                            self.video_dict[user_id] = show_id
                        print(show_id)
                        # data = data.encode('utf-8')
                        # 解码 base64 字符串为字节流
                        frame_data = base64.b64decode(data)
                        np_arr = np.frombuffer(frame_data, np.uint8)  # 使用 OpenCV 解码字节数据为图像
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # 读取为彩色图像
                        if frame is None:
                            print("Error: Failed to decode frame.")
                            return None  # 将 OpenCV 图像（BGR 格式）转换为 QImage（RGB 格式）
                        height, width, channels = frame.shape
                        bytes_per_line = channels * width
                        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                        print("transform to QImage")
                        # 将QImage转换为QPixmap，并显示在QLabel上
                        pixmap = QPixmap.fromImage(q_img)
                        # 获取 QLabel 的大小
                        label_width = self.participants[show_id].width()
                        label_height = self.participants[show_id].height()
                        # 将 QPixmap 缩放到 QLabel 的大小，保持比例
                        scaled_pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio)
                        self.participants[show_id].setPixmap(scaled_pixmap)
                        self.participants[show_id].resize(pixmap.width(), pixmap.height())
                        self.participants[show_id].show()
                    elif message.startswith("video:off"):
                        print(message)
                        user_id = message[len("video:off:"):]
                        print(f"user {user_id} close the video")
                        show_id = self.video_dict.pop(user_id, None)
                        if show_id is not None:
                            self.participants[show_id].clear()
                    elif message.startswith("cancel"):
                        print("The conference is canceled")
                        if self.video_thread.video_enabled:
                            print("mark1")
                            self.video_thread.video_enabled = False
                            self.video_thread.capture.release()
                            self.video_thread.capture = None
                        if self.audio_thread.audio_enabled:
                            print("mark2")
                            self.audio_thread.audio_enabled = False
                            self.audio_thread.stream.stop_stream()
                            print("mark3")
                            self.audio_thread.stop_stream = None
                        #print("mark4")
                        self.close()
                    else:
                        print("Unknown message")
            except Exception as e:
                print(f"Error listening for messages: {e}")
                break

    def listen_for_audio(self):
        """ 在后台线程中监听 WebSocket 消息 """
        while True:
            try:
                message = self.audio_ws.recv()  # 接收来自服务器的消息
                if message:
                    print("receive a message")
                    if message.startswith("audio:"):
                        datas = message.split(":")
                        user_id = datas[1]
                        print(f"user_id = {user_id}")
                        data = datas[2]
                        print(f"receive a audio from {user_id}")
                        frame_data = base64.b64decode(data)
                        self.audio_output.write(frame_data)
                    else:
                        print("Unknown message")
            except Exception as e:
                print(f"Error listening for messages: {e}")
                break

    def upload_file(self):
        """ 上传文件并显示文件名 """
        file_name, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*)")
        if file_name:
            self.chat_list.addItem(f"你上传了文件: {file_name}")

    def end_meeting(self):
        # 创建一个消息框，询问是否确定要结束会议
        reply = QMessageBox.question(self, '结束会议', '确定要结束会议吗？此操作将结束所有与会者的连接。',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # 如果用户选择“是”，执行结束会议操作
        if reply == QMessageBox.Yes:
            # 你可以在这里加入与服务器通信的代码，通知所有与会者会议已经结束
            url = f'http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/cancel-meeting'
            data = {
                "user_id": self.user_id,
                "conference_id": self.conference_id
            }
            try:
                response = requests.post(url, json=data)
                if response.json()["status"] == "success":
                    print("markhhh")
                    if self.video_thread.video_enabled:
                        self.video_thread.video_enabled = False
                        self.video_thread.capture.release()
                        self.video_thread.capture = None
                    if self.audio_thread.audio_enabled:
                        self.audio_thread.audio_enabled = False
                        self.audio_thread.stream.stop_stream()
                        #self.audio_thread.stream = None
                    print("结束会议成功")
                    self.close()  # 关闭当前窗口，或者做其他清理工作
                else:
                    QMessageBox.warning(self, 'Error', f'Message: {response.json()["message"]}')
                    print("结束会议失败")
            except Exception as e:
                print(f"Error quitting meeting: {e}")
        else:
            print("取消结束会议")  # 如果用户选择“否”，可以在这里做一些处理

    def exit_meeting(self):
        # 创建一个消息框，询问是否确认退出会议
        reply = QMessageBox.question(self, '退出会议', '确定要退出会议吗？', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        # 如果用户选择“是”，执行退出操作
        if reply == QMessageBox.Yes:
            # if self.video_thread.capture != None:
            #     self.video_thread.video_enabled = False
            #     self.video_thread.capture.release()
            #     self.video_thread.capture = None
            # if self.audio_thread.stream != None:
            #     self.audio_thread.audio_enabled = False
            #     self.audio_thread.stream.stop_stream()
            #     self.audio_thread.stop_stream = None

            if self.video_thread.video_enabled:
                self.video_thread.video_enabled = False
                self.video_thread.capture.release()
                self.video_thread.capture = None
            if self.audio_thread.audio_enabled:
                self.audio_thread.audio_enabled = False
                self.audio_thread.stream.stop_stream()
                self.audio_thread.stop_stream = None
            url = f'http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/quit-meeting'
            data = {
                "user_id": self.user_id,
                "conference_id": self.conference_id
            }
            try:
                response = requests.post(url, json=data)
                if response.json()["status"] == "success":
                    print("退出会议成功")
                    self.close()  # 关闭当前窗口
                else:
                    print("退出会议失败")
            except Exception as e:
                print(f"Error quitting meeting: {e}")
        else:
            print("取消退出会议")  # 如果用户选择“否”，可以在这里做一些处理

    # Toggle Audio (Mute/Unmute)
    def toggle_audio(self):
        """ 切换音频状态 """
        self.audio_toggle_count += 1  # 每次点击递增计数器

        if self.audio_toggle_count % 2 == 1:  # 单数次点击，开麦
            self.audio_button.setIcon(self.audio_icon_on)  # 设置开麦图标
            self.audio_enabled = True
        else:  # 双数次点击，闭麦
            self.audio_button.setIcon(self.audio_icon_off)  # 设置静音图标
            self.audio_enabled = False

        # 启动或关闭音频流
        self.audio_thread.toggle_audio(self.audio_enabled)

    def toggle_video(self):
        """ 切换视频状态 """
        self.video_toggle_count += 1  # 每次点击递增计数器

        if self.video_toggle_count % 2 == 1:  # 单数次点击，开启摄像头
            self.video_button.setIcon(self.video_icon_on)  # 设置开启摄像头图标
            self.video_enabled = True
        else:  # 双数次点击，关闭摄像头
            self.video_button.setIcon(self.video_icon_off)  # 设置关闭摄像头图标
            self.video_enabled = False
            # print("send video off")
            # self.ws.send("video:off")

        # 启动或关闭视频流
        self.video_thread.toggle_video(self.video_enabled)

    def update_camera_frame(self):
        """ 捕获并更新视频帧 """
        if self.video_thread.video_enabled:
            # print("update camera image")
            ret, frame = self.video_thread.capture.read()  # 捕获一帧
            if not ret:
                print("Error: Failed to capture image.")
                return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 将图像转换为QImage对象
            height, width, channel = frame.shape
            bytes_per_line = channel * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            # 将QImage转换为QPixmap，并显示在QLabel上
            pixmap = QPixmap.fromImage(q_img)
            self.participants[0].setPixmap(pixmap)
            self.participants[0].resize(pixmap.width(), pixmap.height())
            self.participants[0].show()
        else:
            self.participants[0].clear()

    def create_video_area(self):
        """创建视频区域"""
        self.video_area = QWidget()
        self.video_layout = QVBoxLayout()
        self.video_area.setLayout(self.video_layout)

        # 写死 3 个参会者
        self.participants = [
            self.create_participant_label("参会者 1"),
            self.create_participant_label("参会者 2"),
            self.create_participant_label("参会者 3"),
        ]

        # 模拟参会者占位符
        self.create_mock_participants(10)

        # 默认演讲者模式
        self.set_speaker_mode()

        self.video_area.setStyleSheet("background-color: #ffffff;")
        return self.video_area

    def create_participant_label(self, name):
        """创建参会者占位符"""
        label = QLabel()
        label.setFixedSize(150, 100)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                color: #0366d6;
                font-size: 12px;
            }
        """)
        label.setText(name)
        return label

    def create_mock_participants(self, count):
        """创建参会者占位符"""
        for i in range(count):
            label = QLabel()
            label.setFixedSize(150, 100)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #ffffff;
                    border: 1px solid #d0d7de;
                    border-radius: 6px;
                    color: #0366d6;
                    font-size: 12px;
                }
            """)
            label.setText(f"参会者 {i + 1}")
            self.participants.append(label)

    def set_speaker_mode(self):
        ## 写死 3 个参会者,链接后端后删除这部分代码
        self.participants = [
            self.create_participant_label("参会者 1"),
            self.create_participant_label("参会者 2"),
            self.create_participant_label("参会者 3"),
        ]
        ##
        """设置演讲者模式"""
        self.clear_video_layout()

        # 演讲者
        speaker_view = self.participants[0]
        speaker_view.setFixedSize(700, 500)
        self.video_layout.addWidget(speaker_view, alignment=Qt.AlignCenter)

        # 小视图（最多显示5个）
        small_views_layout = QHBoxLayout()
        max_small_views = 3  # 最多显示5个参会者
        for i, participant in enumerate(self.participants[1:]):  # 跳过演讲者本身
            if i >= max_small_views:  # 超过5个则忽略
                break
            participant.setFixedSize(350, 250)  # 小视图固定大小
            small_views_layout.addWidget(participant)

        self.video_layout.addLayout(small_views_layout)

    def set_equal_mode(self):
        ## 写死 3 个参会者,链接后端后删除这部分代码
        self.participants = [
            self.create_participant_label("参会者 1"),
            self.create_participant_label("参会者 2"),
            self.create_participant_label("参会者 3"),
        ]
        ##

        """设置等分模式"""
        self.clear_video_layout()

        grid_layout = QGridLayout()
        cols = 3
        for index, participant in enumerate(self.participants):
            participant.setFixedSize(150, 100)
            grid_layout.addWidget(participant, index // cols, index % cols)
        self.video_layout.addLayout(grid_layout)

    def toggle_view_mode(self):
        """切换视图模式（单数次为等分模式，双数次为演讲者模式）"""
        self.view_toggle_count += 1  # 每次点击递增计数器

        if self.view_toggle_count % 2 == 1:  # 单数次点击：等分模式
            self.set_equal_mode()
        else:  # 双数次点击：演讲者模式
            self.set_speaker_mode()

    def clear_video_layout(self):
        """清空视频布局"""
        while self.video_layout.count():
            child = self.video_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MeetingWindow(1, 2)

    window.show()
    sys.exit(app.exec_())
