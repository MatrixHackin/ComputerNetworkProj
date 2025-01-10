import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor
import json


from PyQt5.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from client.ui.conf_window import MeetingWindow
from client.config import *
import asyncio
import websockets

global user_id

# 创建会议的弹窗
class CreateMeetingDialog(QDialog):
    # 定义信号，用于通知主窗口加入会议成功
    create_meeting_success = pyqtSignal(int, int)  # 参数是 conference_id 和 user_id
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Create Meeting")
        self.setWindowIcon(QIcon("ui/resources/icon.png"))
        self.setFixedSize(800, 300)
        self.setStyleSheet("""
            QDialog {
                font-family: Arial, sans-serif;
                font-size: 32px;
            }
            QLabel {
                font-weight: bold;
                font-family: Arial, sans-serif;
                font-size: 32px;
            }
            QLineEdit {
                font-family: Arial, sans-serif;
                font-size: 25px;
                border: 1px solid #994c00;
                border-radius: 5px;
            }
            QPushButton {
                font-family: Arial, sans-serif;
                font-size: 32px;
                background-color: #994c00;
                color: white;
                font-weight: bold;z
                border-radius: 10px;
                border-color: #4c5caf;
            }
            QPushButton:hover {
                background-color: #4c5caf;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        # 创建标题
        self.title_label = QLabel("Create Meeting")
        self.title_label.setStyleSheet("""
                    font-size: 40px;
                    color: #994c00;
                    font-weight: bold;
                """)
        self.conference_name_label = QLabel("Conference Name:")
        self.conference_name_input = QLineEdit()
        self.conference_name_input.setPlaceholderText("Enter the conference name")
        self.conference_name_input.setFixedSize(400, 50)

        self.conference_password_label = QLabel("Conference Password:")
        self.conference_password_input = QLineEdit()
        self.conference_password_input.setPlaceholderText("Enter the conference password")
        self.conference_password_input.setEchoMode(QLineEdit.Password)
        self.conference_password_input.setFixedSize(400, 50)

        self.submit_button = QPushButton("Create Meeting")
        self.submit_button.clicked.connect(self.create_meeting)

        # 创建水平布局，每一行包含标签和输入框
        conference_name_layout = QHBoxLayout()
        conference_name_layout.addWidget(self.conference_name_label)
        conference_name_layout.addWidget(self.conference_name_input)

        conference_password_layout = QHBoxLayout()
        conference_password_layout.addWidget(self.conference_password_label)
        conference_password_layout.addWidget(self.conference_password_input)

        # 创建垂直布局，包含两个水平布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.title_label, alignment=Qt.AlignTop | Qt.AlignHCenter)  # 添加标题并居中
        main_layout.addLayout(conference_name_layout)
        main_layout.addLayout(conference_password_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.submit_button)
        button_layout.addStretch(1)

        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def create_meeting(self):
        conference_name = self.conference_name_input.text()
        conference_password = self.conference_password_input.text()

        if (conference_name==None) | (conference_name=='') | (conference_password==None) | (conference_password==''):
            QMessageBox.warning(self, 'Error', 'Name or Password cannotbe null. Please enter again.')
            return

        payload = {
            "conference_name": conference_name,
            "conference_password": conference_password,
            "host_id": user_id
        }

        response = requests.post(f"http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/create-meeting", json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                self.accept()  # 关闭弹窗
                self.show_message("Meeting created successfully!")
                # # 自动加入会议
                self.join_meeting(conference_name, conference_password)
            else:
                # TODO：显示错误信息，并将input中已输入的会议名和密码清空
                self.show_error_message(f"Error: {result.get('message')}")
                self.clear_input_fields()
                self.show_message(f"Error: {result.get('message')}")
        else:
            self.show_message("Error: Unable to create meeting.")

    def show_error_message(self, message):
        # 使用QMessageBox弹窗显示错误信息
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()()

    def clear_input_fields(self):
        # 清空输入框中的内容
        self.conference_name_input.clear()
        self.conference_password_input.clear()

    def show_message(self, message):
        print(message)

    def join_meeting(self, conference_name, conference_password):
        # 模拟加入会议操作
        payload = {
            "user_id": user_id,
            "conference_name": conference_name,
            "conference_password": conference_password
        }

        headers = {
            "Authorization": "Bearer YOUR_TOKEN"
        }

        response = requests.post(f"http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/join-meeting", json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                self.show_message("Successfully joined the meeting!")
                # 发射信号，通知 MainWindow
                self.create_meeting_success.emit(result.get("conference_id"), user_id)
                # 在这里你可以建立 WebSocket 或其他连接
            else:
                self.show_error_message(f"Error: {result.get('message')}")
                self.clear_input_fields()
                self.show_message(f"Error: {result.get('message')}")
        else:
            self.show_message("Error: Unable to join meeting.")


# 加入会议的弹窗
class JoinMeetingDialog(QDialog):
    # 定义信号，用于通知主窗口加入会议成功
    join_meeting_success = pyqtSignal(int, int)  # 参数是 conference_id 和 user_id
    def __init__(self,meeting_window=None):
        self.meeting_window=meeting_window

        super().__init__()

        self.setWindowTitle("Join Meeting")
        self.setFixedSize(800, 300)
        self.setStyleSheet("""
            QDialog {
                font-family: Arial, sans-serif;
                font-size: 32px;
            }
            QLabel {
                font-weight: bold;
                font-family: Arial, sans-serif;
                font-size: 32px;
            }
            QLineEdit {
                font-family: Arial, sans-serif;
                padding: 10px;
                font-size: 25px;
                border: 1px solid #994c00;
                border-radius: 5px;
            }
            QPushButton {
                font-family: Arial, sans-serif;
                padding: 10px;
                font-size: 32px;
                background-color: #994c00;
                color: white;
                font-weight: bold;z
                border-radius: 10px;
                border-color:#4c5caf
            }
            QPushButton:hover {
                background-color: #4c5caf;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        # 创建标题
        self.title_label = QLabel("Join Meeting")
        self.title_label.setStyleSheet("""
                    font-size: 40px;
                    color: #994c00;
                    font-weight: bold;
                """)
        self.conference_name_label = QLabel("Conference Name:")
        self.conference_name_input = QLineEdit()
        self.conference_name_input.setPlaceholderText("Enter the conference name")
        self.conference_name_input.setFixedSize(400, 50)

        self.conference_password_label = QLabel("Conference Password:")
        self.conference_password_input = QLineEdit()
        self.conference_password_input.setPlaceholderText("Enter the conference password")
        self.conference_password_input.setEchoMode(QLineEdit.Password)
        self.conference_password_input.setFixedSize(400, 50)

        self.submit_button = QPushButton("Join Meeting")
        self.submit_button.clicked.connect(self.join_meeting)

        # 创建水平布局，每一行包含标签和输入框
        conference_name_layout = QHBoxLayout()
        conference_name_layout.addWidget(self.conference_name_label)
        conference_name_layout.addWidget(self.conference_name_input)

        conference_password_layout = QHBoxLayout()
        conference_password_layout.addWidget(self.conference_password_label)
        conference_password_layout.addWidget(self.conference_password_input)

        # 创建垂直布局，包含两个水平布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.title_label, alignment=Qt.AlignTop | Qt.AlignHCenter)  # 添加标题并居中
        main_layout.addLayout(conference_name_layout)
        main_layout.addLayout(conference_password_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.submit_button)
        button_layout.addStretch(1)

        # 添加按钮布局到主布局
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def join_meeting(self):
        conference_name = self.conference_name_input.text()
        conference_password = self.conference_password_input.text()
        if (conference_name==None) | (conference_name=='') | (conference_password==None) | (conference_password==''):
            QMessageBox.warning(self, 'Error', 'Name or Password cannotbe null. Please enter again.')
            return

        payload = {
            "user_id": user_id,
            "conference_name": conference_name,
            "conference_password": conference_password
        }

        response = requests.post(f"http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/join-meeting", json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":

                self.show_message("Successfully joined the meeting!")
                """
                from now begin to websocket connection
                """
                conference_id=result.get("conference_id")
                # 发射信号，通知 MainWindow
                self.join_meeting_success.emit(conference_id, user_id)

                self.accept()  # 关闭弹窗
                # self.open_meeting_window(conference_id,user_id)
            else:
                self.show_error_message(f"Error: {result.get('message')}")
                self.clear_input_fields()
                self.show_message(f"Error: {result.get('message')}")
        else:
            self.show_message("Error: Unable to join meeting.")
            self.conference_name_input.clear()
            self.conference_password_input.clear()
            QMessageBox.warning(self, 'Error', 'Unable to join meeting.')



    def open_meeting_window(self, conference_id,user_id):
        self.meeting_window = MeetingWindow(conference_id,user_id)
        self.meeting_window.show()
        print("111")

    def show_error_message(self, message):
        # 使用QMessageBox弹窗显示错误信息
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()()

    def clear_input_fields(self):
        # 清空输入框中的内容
        self.conference_name_input.clear()
        self.conference_password_input.clear()

    def show_message(self, message):
        print(message)


class MainWindow(QWidget):
    def __init__(self, data = None):
        global user_id
        user_id = data
        super().__init__()

        # 确保 asyncio 事件循环有效
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())

        # 启动 WebSocket 连接
        asyncio.ensure_future(self.connect_to_server())

        self.setWindowTitle(f"Main Page - User ID: {user_id}")
        self.setWindowIcon(QIcon("ui/resources/icon.png"))
        self.setGeometry(900, 500, 500, 500)  # 调整窗口大小
        self.setFixedSize(1200, 600)
        self.meeting_window = None

        # 创建主布局
        main_layout = QVBoxLayout()

        # 创建三栏布局
        content_layout = QHBoxLayout()

        # 左侧栏
        left_layout = QVBoxLayout()

        # 退出登录按钮，圆形按钮
        self.logout_button = QPushButton("Logout")
        self.logout_button.setFixedSize(150, 100)
        self.logout_button.setStyleSheet("""
            QPushButton {
                font-family: Arial, sans-serif;
                padding: 5px;
                font-size: 32px;
                background-color: #994c00;
                color: white;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e5f3ff;
                color:#000000
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)
        self.logout_button.clicked.connect(self.logout)

        self.create_meeting_button = QPushButton("Create\nMeeting")
        self.create_meeting_button.setFixedSize(150, 100)
        self.create_meeting_button.clicked.connect(self.open_create_meeting_dialog)
        self.create_meeting_button.setStyleSheet("""
            QPushButton {
                font-family: Arial, sans-serif;
                padding: 5px;
                font-size: 32px;
                background-color: #994c00;
                color: white;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e5f3ff;
                color:#000000

            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        self.join_meeting_button = QPushButton("Join\nMeeting")
        self.join_meeting_button.setFixedSize(150, 100)
        self.join_meeting_button.clicked.connect(self.open_join_meeting_dialog)

        self.join_meeting_button.setStyleSheet("""
            QPushButton { 
                font-family: Arial, sans-serif;
                padding: 5px;
                font-size: 32px;
                background-color: #994c00;
                color: white;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e5f3ff;     
                color:#000000
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)

        # 添加按钮到左侧栏
        left_layout.addWidget(self.logout_button)
        left_layout.addWidget(self.create_meeting_button)
        left_layout.addWidget(self.join_meeting_button)

        # 设置左侧栏占 15%
        left_frame = QFrame()
        left_frame.setLayout(left_layout)
        left_frame.setFixedWidth(int(self.width() * 0.15))  # 设置左侧栏的宽度

        # 中间栏（我创建的会议）
        middle_layout = QVBoxLayout()
        self.created_meeting_list_label = QLabel("My Can-Join Meetings")
        self.created_meeting_list_label.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 32px;
            font-weight: bold;
        """)

        self.created_meeting_list = QListWidget()
        self.created_meeting_list.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 25px;
            border: 1px solid #994c00;
            border-radius: 10px;
        """)
        self.created_meeting_list.setSpacing(10)  # 设置项目之间的行间距为 10 像素

        middle_layout.addWidget(self.created_meeting_list_label)
        middle_layout.addWidget(self.created_meeting_list)

        # 设置中间栏占 40%
        middle_frame = QFrame()
        middle_frame.setLayout(middle_layout)
        middle_frame.setFixedWidth(int(self.width() * 0.4))  # 设置中间栏的宽度

        # 右侧栏（我加入的会议）
        right_layout = QVBoxLayout()
        self.joined_meeting_list_label = QLabel("My Joined Meetings")
        self.joined_meeting_list_label.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 32px;
            font-weight: bold;
        """)

        self.joined_meeting_list = QListWidget()
        # self.created_meeting_list.setStyle(QStyleFactory.create('Fusion'))
        self.joined_meeting_list.setStyleSheet("""
            font-family: Arial, sans-serif;
            font-size: 25px;
            border: 1px solid #994c00;
            border-radius: 10px;
            margin-bottom: 5px;
        """)
        self.joined_meeting_list.setSpacing(10)  # 设置项目之间的行间距为 10 像素

        right_layout.addWidget(self.joined_meeting_list_label)
        right_layout.addWidget(self.joined_meeting_list)

        # 设置右侧栏占 40%
        right_frame = QFrame()
        right_frame.setLayout(right_layout)
        right_frame.setFixedWidth(int(self.width() * 0.4))  # 设置右侧栏的宽度

        # 添加三个栏到内容布局
        content_layout.addWidget(left_frame)
        content_layout.addWidget(middle_frame)
        content_layout.addWidget(right_frame)

        # 将内容布局添加到主布局
        main_layout.addLayout(content_layout)

        # 更新会议列表
        self.update_meeting_list()

        # 设置主窗口的布局
        self.setLayout(main_layout)

    async def connect_to_server(self):
        print("Connecting to server...")
        # 连接到服务器
        url=f"ws://{SERVER_IP}:{MAIN_SERVER_PORT}/wsconnect"
        try:
            async with websockets.connect(url) as websocket:
                while True:
                    message = await websocket.recv()
                    if message == "update":
                        self.update_meeting_list()
        except Exception as e:
            print(e)


    def update_meeting_list(self):
        # 从服务器获取可加入的会议列表
        print(user_id)
        response_self = requests.get(f"http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/{user_id}/canjoin-meeting-list")
        if response_self.status_code != 200:
            self.show_message("Error: Unable to fetch meeting list.")
            return
        # 更新我创建的可加入会议列表
        response_self = json.loads(response_self.text)
        print(response_self)
        self.created_meeting_list.clear()
        for meeting in response_self["data"]:
            item = f"{meeting['conference_name']}"
            self.created_meeting_list.addItem(item)

        # 更新已加入的会议列表
        overall_response = requests.get(f"http://{SERVER_IP}:{MAIN_SERVER_PORT}/user/{user_id}/joined-meeting-list")
        if overall_response.status_code != 200:
            self.show_message("Error: Unable to fetch meeting list.")
            return
        overall_response = json.loads(overall_response.text)
        self.joined_meeting_list.clear()
        for meeting in overall_response["data"]:
            item = f"{meeting['conference_name']}"
            self.joined_meeting_list.addItem(item)

    def logout(self):
        # 实现退出登录操作
        self.show_message("Logged out successfully.")
        # 实际操作可以跳转到登录界面，清除会话等

    def show_message(self, message):
        print(message)

    def open_create_meeting_dialog(self):
        dialog = CreateMeetingDialog()
        # 连接信号 create_meeting_success 到 MainWindow 的 open_meeting_window 方法
        dialog.create_meeting_success.connect(self.open_meeting_window)
        dialog.exec()
        self.update_meeting_list()

    def open_join_meeting_dialog(self):
        dialog = JoinMeetingDialog()
        # 连接信号 join_meeting_success 到 MainWindow 的 open_meeting_window 方法
        dialog.join_meeting_success.connect(self.open_meeting_window)
        dialog.exec()

    def open_meeting_window(self, conference_id,user_id):
        self.meeting_window = MeetingWindow(conference_id,user_id)
        self.meeting_window.show()
        print("111")

def main():
    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create('cleanlooks'))
    # app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec()())
#
#
# if __name__ == "__main__":
#     main()
