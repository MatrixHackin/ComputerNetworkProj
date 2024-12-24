import sys
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QImage
from client.fuction.video import VideoStreamThread
import cv2
import websocket
import websockets
from client.config import *
import asyncio
import requests
import threading


class MeetingWindow(QWidget):
    # 定义一个信号来更新 UI
    message_received = pyqtSignal(str)

    def __init__(self,conference_id,user_id):
        super().__init__()
        self.conference_id=conference_id
        self.user_id=user_id
        # self.conference_id=1
        # self.user_id=1

        self.setWindowTitle("Meeting Interface")
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
        self.user_video_label = QLabel()  # 当前用户视频的显示区域
        self.timer = QTimer()

        self.initUI()
        self.timer.timeout.connect(self.update_camera_frame)  # 定时器更新摄像头画面
        self.ws = None
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
        url = f"ws://{SERVER_IP}:{MAIN_SERVER_PORT}/ws/{self.conference_id}/{self.user_id}"
        self.ws = websocket.create_connection(url)
        # 创建视频流线程
        self.video_thread = VideoStreamThread(self.ws)
        self.video_thread.start()
        # 启动后台线程来监听服务器消息
        listen_thread = threading.Thread(target=self.listen_for_messages)
        listen_thread.daemon = True  # 后台线程，当主线程结束时自动结束
        listen_thread.start()

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
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff; /* 白色背景 */
                border: none; /* 无边框 */
                padding: 10px; /* 内边距 */
                font-size: 14px;
                color: #24292e; /* 深灰色字体 */
            }
            QListWidget::item {
                margin: 5px 0; /* 项目之间的间距 */
                padding: 10px;
                background-color: #f6f8fa; /* 条目背景 */
                border: 1px solid #d0d7de;
                border-radius: 4px;
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
            self.ws.send(f"broadcast:[{time}] {message}")
            self.text_input.clear()

    def listen_for_messages(self):
        """ 在后台线程中监听 WebSocket 消息 """
        while True:
            try:
                message = self.ws.recv() # 接收来自服务器的消息
                if message:
                    print(message)
                    self.chat_list.addItem(f"{message}")
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
            print("结束会议")  # 在此可以执行结束会议的逻辑
            # 你可以在这里加入与服务器通信的代码，通知所有与会者会议已经结束
            self.close()  # 关闭当前窗口，或者做其他清理工作
        else:
            print("取消结束会议")  # 如果用户选择“否”，可以在这里做一些处理

    def exit_meeting(self):
        # 创建一个消息框，询问是否确认退出会议
        reply = QMessageBox.question(self, '退出会议', '确定要退出会议吗？',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # 如果用户选择“是”，执行退出操作
        if reply == QMessageBox.Yes:
            print("退出会议")  # 你可以根据实际需求在这里实现退出逻辑
            self.close()  # 关闭当前窗口
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

    def toggle_video(self):
        """ 切换视频状态 """
        self.video_toggle_count += 1  # 每次点击递增计数器

        if self.video_toggle_count % 2 == 1:  # 单数次点击，开启摄像头
            self.video_button.setIcon(self.video_icon_on)  # 设置开启摄像头图标
            self.video_enabled = True
        else:  # 双数次点击，关闭摄像头
            self.video_button.setIcon(self.video_icon_off)  # 设置关闭摄像头图标
            self.video_enabled = False

        # 启动或关闭视频流
        self.video_thread.toggle_video(self.video_enabled)

    def update_camera_frame(self):
        """ 捕获并更新视频帧 """
        if self.video_enabled:
            ret, frame = self.capture.read()  # 捕获一帧
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
        for participant in self.participants:
            self.video_layout.addWidget(participant)
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
        speaker_view.setFixedSize(1000, 667)
        self.video_layout.addWidget(speaker_view, alignment=Qt.AlignCenter)

        # 小视图（最多显示5个）
        small_views_layout = QHBoxLayout()
        max_small_views = 5  # 最多显示5个参会者
        for i, participant in enumerate(self.participants[1:]):  # 跳过演讲者本身
            if i >= max_small_views:  # 超过5个则忽略
                break
            participant.setFixedSize(150, 100)  # 小视图固定大小
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
        cols = 5
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
    window = MeetingWindow(1,2)

    window.show()
    sys.exit(app.exec_())
