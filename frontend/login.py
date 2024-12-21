import sys
import requests
import hashlib

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox
import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


class App(QWidget):
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

    def register(self):
        url = 'http://127.0.0.1:8888/register'
        username = self.username_input.text()
        password = self.password_input.text()
        password = hashlib.sha256(password.encode()).hexdigest()
        data = {
            "action": "register",
            "username": username,
            "password": password
        }
        try:
            print(f"Registering user: {data}")
            response = requests.post(url, json=data)
            if response.status_code == 200:
                QMessageBox.information(self, 'Success', 'Registration successful!')
            else:
                self.clear_input_fields()
                QMessageBox.warning(self, 'Error', f'Message: {response.text}')
        except requests.RequestException as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def login(self):
        url = 'http://127.0.0.1:8888/login'
        username = self.username_input.text()
        password = self.password_input.text()
        password = hashlib.sha256(password.encode()).hexdigest()
        data = {
            "action": "login",
            "username": username,
            "password": password
        }
        try:
            print(f"Registering user: {data}")
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    QMessageBox.information(self, 'Success', 'Login successful!')
                    print("Token:", response.json())
                else:
                    self.clear_input_fields()
                    QMessageBox.warning(self, 'Error', f'Message: {response.text}')
            else:
                print("Error: Unable to login.")
        except requests.RequestException as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def clear_input_fields(self):
        # 清空输入框中的内容
        self.password_input.clear()
        self.username_input.clear()

    def exit_app(self):
        print("Exiting application...")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
