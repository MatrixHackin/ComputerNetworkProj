import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, \
    QFileDialog, QLineEdit, QTextEdit, QScrollArea, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon  # 导入 QIcon 用于加载图标
from PyQt5.QtCore import QSize  # 导入 QSize 用于调整图标大小
import json
import time
import websocket
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QWidget, QFileDialog


class MeetingWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Meeting Interface")
        self.setFixedSize(1920, 1080)  # Full screen

        self.audio_enabled = True
        self.video_enabled = True
        self.owner_view = True
        self.speaker_view = False

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()

        # Left Sidebar with Audio and Video buttons
        left_sidebar_widget = self.create_left_sidebar()  # Create left sidebar widget
        left_sidebar_widget.setFixedWidth(int(self.width() * 0.074))

        # Chat area (right side)
        chat_area = self.create_chat_area()
        chat_area.setFixedWidth(int(self.width() * 0.3))

        # Video area (centered in the window)
        video_area = self.create_video_area()

        # Main Layout
        main_layout.addWidget(left_sidebar_widget)  # Add the widget, not just the layout
        main_layout.addWidget(video_area)
        main_layout.addWidget(chat_area)  # Use addWidget instead of addLayout

        self.setLayout(main_layout)

    def create_left_sidebar(self):
        sidebar_layout = QVBoxLayout()

        # Audio Button with icon (圆形按钮)
        self.audio_button = QPushButton()
        self.audio_icon_off = QIcon("frontend/img/audio_off_icon.png")  # 静音图标
        self.audio_icon_on = QIcon("frontend/img/audio_on_icon.png")  # 开启麦克风图标
        self.audio_button.setIcon(self.audio_icon_off)  # 默认静音
        # self.audio_button.setStyleSheet("""
        #     border: 1px solid black;
        #     font-size: 20px;
        #     padding: 0px;  # 去除多余的内边距
        #     width: 80px;  # 设置按钮宽度
        #     height: 80px;  # 设置按钮高度
        #     border-radius: 40px;  # 设置圆角为半径的值，形成圆形按钮
        #     background-color: #4CAF50;  # 设置背景颜色（可以根据需要调整）
        # """)
        self.audio_button.setIconSize(QSize(80, 80))  # 设置图标大小
        self.audio_button.clicked.connect(self.toggle_audio)

        # Video Button with icon (圆角方形按钮)
        self.video_button = QPushButton()
        # self.video_button.setStyleSheet("""
        #     border: 1px solid black;
        #     font-size: 20px;
        #     padding: 0px;  # 去除多余的内边距
        #     width: 60px;  # 设置按钮宽度
        #     height: 60px;  # 设置按钮高度
        #     border-radius: 15px;  # 设置圆角为15px，形成圆角方形按钮
        #     background-color: #008CBA;  # 设置背景颜色（可以根据需要调整）
        # """)
        self.video_icon_off = QIcon("frontend/img/video_off_icon.png")  # 关闭摄像头图标
        self.video_icon_on = QIcon("frontend/img/video_on_icon.png")  # 开启摄像头图标
        self.video_button.setIcon(self.video_icon_off)  # 默认关闭摄像头
        self.video_button.setIconSize(QSize(80, 80))  # 设置图标大小
        self.video_button.clicked.connect(self.toggle_video)

        # Add buttons to the sidebar layout
        sidebar_layout.addWidget(self.audio_button)
        sidebar_layout.addWidget(self.video_button)
        sidebar_layout.addStretch()

        # Create a QWidget to hold the layout
        sidebar_widget = QWidget()  # Wrap the layout inside a QWidget
        sidebar_widget.setLayout(sidebar_layout)  # Set layout to the widget

        return sidebar_widget  # Return the widget

    # Toggle Audio (Mute/Unmute)
    def toggle_audio(self):
        if self.audio_enabled:
            self.audio_button.setIcon(self.audio_icon_off)  # 设置静音图标
            self.audio_enabled = False
        else:
            self.audio_button.setIcon(self.audio_icon_on)  # 设置开麦图标
            self.audio_enabled = True

    # Toggle Video (Mute/Unmute)
    def toggle_video(self):
        if self.video_enabled:
            self.video_button.setIcon(self.video_icon_off)  # 设置关闭摄像头图标
            self.video_enabled = False
        else:
            self.video_button.setIcon(self.video_icon_on)  # 设置开启摄像头图标
            self.video_enabled = True

    def create_video_area(self):
        video_area = QWidget()
        video_area_layout = QVBoxLayout()

        # Placeholder image for video area
        placeholder_image = QLabel()
        placeholder_image.setPixmap(QPixmap("frontend/img/placeholder.png").scaled(800, 600, Qt.KeepAspectRatio))
        placeholder_image.setAlignment(Qt.AlignCenter)

        video_area_layout.addWidget(placeholder_image)

        video_area.setLayout(video_area_layout)
        video_area.setFixedSize(800, 600)

        return video_area

    def create_chat_area(self):
        chat_layout = QVBoxLayout()

        # 显示 WebSocket 地址
        self.ws_label = QLabel("wss://server_ip:conference_port:/chat")
        self.ws_label.setAlignment(Qt.AlignCenter)
        self.ws_label.setStyleSheet("font-size: 20px; padding: 10px;")
        chat_layout.addWidget(self.ws_label)

        # Chat Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat Messages...")
        self.chat_display.setStyleSheet("font-size: 20px; padding: 10px;")
        chat_layout.addWidget(self.chat_display)

        # Message input field
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter your message...")
        self.message_input.setStyleSheet("font-size: 20px; padding: 10px;")
        chat_layout.addWidget(self.message_input)

        # Send Message Button
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("font-size: 20px; padding: 10px;")
        self.send_button.clicked.connect(self.send_message)
        chat_layout.addWidget(self.send_button)

        # File upload
        file_button = QPushButton("Send File")
        file_button.setStyleSheet("font-size: 20px; padding: 10px;")
        file_button.clicked.connect(self.send_file)
        chat_layout.addWidget(file_button)

        chat_layout.addStretch()

        # Create a QWidget to hold the layout
        chat_area_widget = QWidget()
        chat_area_widget.setLayout(chat_layout)

        return chat_area_widget

    def send_message(self):
        message_text = self.message_input.text()
        if message_text:
            timestamp = time.time()
            message_data = {
                "sender": "ALICE",  # Replace with actual sender name
                "message": message_text,
                "timestamp": timestamp
            }
            if self.ws:
                self.ws.send(json.dumps(message_data))  # Send message to WebSocket server
            self.chat_display.append(f"Me: {message_text}")  # Display the message in the chat area
            self.message_input.clear()  # Clear input field

    def connect_to_websocket(self, url):
        """ Connect to the WebSocket server. """

        def on_message(ws, message):
            message_data = json.loads(message)
            sender = message_data.get("sender", "Unknown")
            message = message_data.get("message", "")
            self.chat_display.append(f"{sender}: {message}")  # Display the incoming message

        def on_error(ws, error):
            print(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("WebSocket closed")

        def on_open(ws):
            print("WebSocket connection established")

        self.ws = websocket.WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        self.ws.on_open = on_open
        self.ws.run_forever()  # Block the main thread to maintain the WebSocket connection

    def send_file(self):
        """ Handle file sending logic. """
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.bmp *.jpeg);;Text Files (*.txt);;All Files (*)")
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            print(f"Sending file: {files[0]}")  # Implement the actual file sending logic here
            # If you need to send the file over the WebSocket, you could use `self.ws.send()` to send the file
            # Example: ws.send(files[0]) or send the file's content as a binary


    def update_video_area(self):
        if self.audio_enabled:
            if self.speaker_view:
                # Replace the placeholder image with speaker's view
                self.show_speaker_view()
            else:
                # Show the owner's view if no one is speaking
                self.show_owner_view()

    def show_owner_view(self):
        print("Showing owner view")

    def show_speaker_view(self):
        print("Showing speaker's view")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MeetingWindow()
    window.show()
    sys.exit(app.exec_())
