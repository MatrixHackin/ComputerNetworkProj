import base64
import os

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

import jwt
from datetime import datetime, timedelta

Base = declarative_base()


# 生成一个32字节的随机字节串
random_bytes = os.urandom(32)
# 将随机字节串转换为Base64编码的字符串（去掉'='填充字符和换行符）
secret_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
SECRET_KEY = secret_key  # 这应该是一个安全的随机字符串
ALGORITHM = 'HS256'  # 使用HMAC SHA-256算法
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 令牌有效期（分钟）


class DBUsers(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True)  # 确保用户名唯一
    password = Column(String, index=True)
    # ip = Column(String, index=True)
    # port = Column(Integer, index=True)


class User(BaseModel):
    action: str
    username: str
    password: str


# 用户服务类，用于封装注册、登录等逻辑
class UserService:
    def __init__(self, get_db: callable):
        self.get_db = get_db

    @staticmethod
    def register(request: User, db: Session):
        user = db.query(DBUsers).filter(request.username == DBUsers.username).first()
        if user is None:
            new_user = DBUsers(username=request.username, password=request.password)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已经被占用，请换用户名",
            )



    @staticmethod
    def login(request : User, db: Session):
        print('enter login:'+request.username+', '+request.password)
        # 检查用户是否存在
        user = db.query(DBUsers).filter(request.username == DBUsers.username, request.password == DBUsers.password).first()
        if user is None:
            if db.query(DBUsers).filter(request.username == DBUsers.username).first() is None:
                print("已进入")
                return {"status": "fail",
                        "message": "No such User"}
            else:
                return {"status": "fail",
                        "message": "wrong password",}
        
        # 生成JWT
        access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.encode({
            'sub': user.username,  # 主题，通常是用户的唯一标识符
            'exp': access_token_expires  # 过期时间
        }, SECRET_KEY, algorithm=ALGORITHM)

        print(f"生成的Token = {access_token}")
        return {"status": "success",
                "message": "Login successful.", 
                "access_token": access_token, 
                "token_type": "bearer"}
