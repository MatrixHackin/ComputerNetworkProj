from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session

from manage_db import manage_db
from user_service import User, UserService

app = FastAPI()

# 创建数据库处理实例
db_manager = manage_db()

# 创建用户管理实例，并注入数据库获取函数
user_manager = UserService(db_manager.get_db)


# 依赖项函数，用于从 get_db 工厂函数中获取数据库会话
def get_db(db: Session = Depends(db_manager.get_db)):
    return db


# 注册接口
@app.post("/register/")
async def register(user: User, db: Session = Depends(get_db)):
    # # 提取请求的 URL 和客户端信息
    # # 获取客户端 IP
    # client_ip = request.client.host
    # # 获取请求的端口
    # client_port = request.client.port
    # # 获取请求的完整 URL
    # url = str(request.url)
    # print("client_ip: client_ip, client_port: client_port, url: full_url")
    return user_manager.register(user, db)


# 登录接口
@app.post("/login")
async def login(user: User, db: Session = Depends(get_db)):
    return user_manager.login(user, db)


# 主程序启动入口
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
