import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, \
    QMainWindow, QListWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import websocket
import json


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口标题、图标和大小
        self.setWindowTitle("Login")
        self.setWindowIcon(QIcon("frontend/img/icon.png"))
        self.setGeometry(900, 500, 500, 500)

        # 创建主水平布局
        main_layout = QHBoxLayout()

        # 左栏布局 (背景和介绍文字)
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.intro_label = QLabel("")
        self.intro_label.setAlignment(Qt.AlignCenter)
        self.intro_label.setFixedWidth(500)
        self.intro_label.setFixedHeight(500)
        self.intro_label.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 40px;
            font-weight: bold;
            padding: 10px;
            background: url("frontend/img/background_image.png");
            background-repeat: no-repeat;
            background-size: cover;
            border-radius: 10px;
            border: 2px solid #ccc;
        """)
        left_layout.addWidget(self.intro_label)
        left_widget.setLayout(left_layout)

        # 设置背景颜色
        left_widget.setStyleSheet("background-color: #f0f0f0;")

        # 右栏布局 (登录界面)
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        self.slogan = QLabel(
            "Welcome to\nMEME Meeting Rooms!\nPlease enter your credentials to \nlog in or register an account.\n")
        self.slogan.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 32px;
            font-weight: bold;
            color: #994c00;
        """)
        self.slogan.setAlignment(Qt.AlignCenter)

        # 用户名和输入框放在同一行
        self.username_label = QLabel("Username:")
        self.username_label.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 32px;
            font-weight: bold;
            color: #994c00;
        """)
        self.username_input = QLineEdit()
        self.username_input.setStyleSheet(
            "font-family: Arial, sans-serif;"
            "font-size: 32px"
            "; padding: 10px;"
            " border: 1px solid #ccc;"
            " border-radius: 5px;")

        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_label)
        username_layout.addWidget(self.username_input)

        # 密码和输入框放在同一行
        self.password_label = QLabel("Password:")
        self.password_label.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 32px;
            font-weight: bold;
            color: #994c00;
        """)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # 默认密码隐藏
        self.password_input.setStyleSheet(
            "font-family: Arial, sans-serif;"
            "font-size: 32px;"
            " padding: 5px;"
            " border: 1px solid #ccc;"
            " border-radius: 5px;")

        # 创建一个显示/隐藏密码的按钮
        self.show_password_button = QPushButton()
        self.show_password_button.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 16px;
            color: #994c00;
            background: transparent;
            border: none;
        """)

        # 设置初始图标为“隐藏密码”图标
        self.show_password_button.setIcon(QIcon("frontend/img/pswd_hide.png"))

        # 连接按钮点击事件
        self.show_password_button.clicked.connect(self.toggle_password_visibility)

        # 创建密码输入框布局
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_label)
        password_layout.addWidget(self.show_password_button)
        password_layout.addWidget(self.password_input)

        # 登录与注册按钮
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                padding-up: 10px;
                font-family: Arial, sans-serif;
                background-color: #994c00;
                color: white;
                font-size: 32px;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #4c5caf;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        self.register_button = QPushButton("Register")
        self.register_button.setStyleSheet("""
            QPushButton {
                font-family: Arial, sans-serif;
                background-color: #994c00;
                color: white;
                font-size: 32px;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #4c5caf;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        # 设置用户名输入框的高度和宽度
        self.username_input.setFixedHeight(50)  # 设置固定高度
        self.username_input.setFixedWidth(400)  # 设置固定宽度

        # 设置密码输入框的高度和宽度
        self.password_input.setFixedHeight(50)  # 设置固定高度
        self.password_input.setFixedWidth(400)  # 设置固定宽度

        # 错误信息
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("font-size: 16px; color: #FF0000;")

        # 添加控件到右栏布局
        right_layout.addWidget(self.slogan)
        right_layout.addLayout(username_layout)  # 使用新的用户名布局
        right_layout.addLayout(password_layout)  # 添加密码布局
        right_layout.addWidget(self.login_button)
        right_layout.addWidget(self.register_button)
        right_layout.addWidget(self.message_label)

        right_widget.setLayout(right_layout)

        # 添加左栏和右栏到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # 设置主布局
        self.setLayout(main_layout)

        # 连接信号
        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

    def toggle_password_visibility(self):
        # 切换密码的显示状态
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)  # 显示密码
            self.show_password_button.setIcon(QIcon("frontend/img/pswd_show.png"))  # 更新按钮文本为 "Hide"
        else:
            self.password_input.setEchoMode(QLineEdit.Password)  # 隐藏密码
            self.show_password_button.setIcon(QIcon("frontend/img/pswd_hide.png"))  # 更新按钮文本为 "Show"

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        payload = {
            "action": "login",
            "username": username,
            "password": password
        }

        response = requests.post("https://server_ip:8888/login", json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                self.message_label.setText("Login successful!")
                token = result.get("token")
                self.store_token(token)
                self.connect_websocket(token)

                # 联动进入主界面
                self.open_main_window()
            else:
                self.message_label.setText(f"Login failed: {result.get('message')}")
        else:
            self.message_label.setText("Login failed: Unable to connect to server.")

    def open_main_window(self):
        # 创建并显示主界面
        self.main_window = MainWindow()  # 这里使用导入的MainWindow类
        self.main_window.show()

        # 关闭登录界面
        self.close()

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        payload = {
            "action": "register",
            "username": username,
            "password": password
        }

        response = requests.post("https://server_ip:8888/register", json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                self.message_label.setText("Registration successful!")
            else:
                self.message_label.setText(f"Registration failed: {result.get('message')}")
        else:
            self.message_label.setText("Registration failed: Unable to connect to server.")

    def store_token(self, token):
        with open("token.txt", "w") as token_file:
            token_file.write(token)

    def connect_websocket(self, token):
        def on_message(ws, message):
            print(f"Received message: {message}")

        def on_error(ws, error):
            print(f"Error: {error}")

        def on_close(ws):
            print("Closed WebSocket connection")

        def on_open(ws):
            print("WebSocket connection established")
            ws.send(json.dumps({"action": "authenticate", "token": token}))

        ws_url = "wss://server_ip:8888/websocket"
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()


class MainWindow(QWidget):
    class MeetingApp(QWidget):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("Main")
            self.setWindowIcon(QIcon("frontend/img/icon.png"))
            self.setGeometry(900, 500, 500, 500)

            # 主布局（左右分栏）
            main_layout = QHBoxLayout()

            # 左栏布局：创建会议和加入会议按钮
            left_widget = QWidget()
            left_layout = QVBoxLayout()

            self.create_meeting_button = QPushButton("Create Meeting")
            self.create_meeting_button.setStyleSheet("""
                QPushButton {
                    font-family: Arial, sans-serif;
                    font-size: 32px;
                    background-color: #994c00;
                    color: white;
                    border-radius: 10px;
                    padding: 15px;
                }
                QPushButton:hover {
                    background-color: #4c5caf;
                }
            """)
            self.create_meeting_button.clicked.connect(self.create_meeting)

            self.join_meeting_button = QPushButton("Join Meeting")
            self.join_meeting_button.setStyleSheet("""
                QPushButton {
                    font-family: Arial, sans-serif;
                    font-size: 32px;
                    background-color: #994c00;
                    color: white;
                    border-radius: 10px;
                    padding: 15px;
                }
                QPushButton:hover {
                    background-color: #4c5caf;
                }
            """)
            self.join_meeting_button.clicked.connect(self.join_meeting)

            left_layout.addWidget(self.create_meeting_button)
            left_layout.addWidget(self.join_meeting_button)

            left_widget.setLayout(left_layout)

            # 右栏布局：显示正在进行的会议列表
            right_widget = QWidget()
            right_layout = QVBoxLayout()

            self.meeting_list_label = QLabel("Ongoing Meetings")
            self.meeting_list_label.setStyleSheet("""
                font-family: Arial, sans-serif;
                font-size: 32px;
                font-weight: bold;
                color: #994c00;
            """)
            self.meeting_list_label.setAlignment(Qt.AlignCenter)

            self.meeting_list_widget = QListWidget()
            self.meeting_list_widget.setStyleSheet("""
                QListWidget {
                    font-family: Arial, sans-serif;
                    font-size: 20px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)

            right_layout.addWidget(self.meeting_list_label)
            right_layout.addWidget(self.meeting_list_widget)

            right_widget.setLayout(right_layout)

            # 添加左右栏到主布局
            main_layout.addWidget(left_widget)
            main_layout.addWidget(right_widget)

            # 设置主布局
            self.setLayout(main_layout)

        def create_meeting(self):
            # 模拟创建会议，展示在右栏的会议列表中
            meeting_name = "Meeting " + str(len(self.meeting_list_widget.items()) + 1)
            self.meeting_list_widget.addItem(meeting_name)
            print(f"Created {meeting_name}")

        def join_meeting(self):
            # 模拟加入会议，展示在右栏的会议列表中
            meeting_name = "Meeting " + str(len(self.meeting_list_widget.items()) + 1)
            self.meeting_list_widget.addItem(meeting_name)
            print(f"Joined {meeting_name}")


def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
