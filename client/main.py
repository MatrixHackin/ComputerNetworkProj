import sys
from PyQt5.QtWidgets import QApplication
from client.ui.login_window import LoginWindow
import asyncio
from qasync import QEventLoop

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 使用 qasync 的 QEventLoop 替代 asyncio 默认事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)  # 将 QEventLoop 设置为 asyncio 的事件循环

    # 创建并显示登录窗口
    login_window = LoginWindow()
    login_window.show()

    # 启动应用程序
    with loop:
        sys.exit(loop.run_forever())