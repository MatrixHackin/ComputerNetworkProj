from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session

from model.database_init import ManageDB
from service.user_service import UserRequest, UserService

app = FastAPI()

# 创建数据库处理实例
db_manager = ManageDB()

# 创建用户管理实例，并注入数据库获取函数
user_manager = UserService(db_manager.get_db)
conference_manager = ConferenceService(db_manager.get_db)

# 依赖项函数，用于从 get_db 工厂函数中获取数据库会话
def get_db(db: Session = Depends(db_manager.get_db)):
    return db

# 注册接口
@app.post("/register/")
async def register(user: UserRequest, db: Session = Depends(get_db)):
    return user_manager.register(user, db)

# 登录接口
@app.post("/login")
async def login(user: UserRequest, db: Session = Depends(get_db)):
    return user_manager.login(user, db)

# 主程序启动入口
if __name__ == "__main__":
    uvicorn.run(app, host="10.26.194.204", port=8888)