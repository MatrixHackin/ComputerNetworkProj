import base64
import os
from typing import Dict

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from server.model.models import DBUsers
from server.model.database_init import ManageDB

# UserRequest DataType
class UserRequest(BaseModel):
    action: str
    username: str
    password: str

db_manager=ManageDB()
class UserService:
    def __init__(self, get_db: callable):
        self.get_db = get_db
        self.client_ip: Dict[str, str] = {}

    @staticmethod
    def register(request: UserRequest, db: Session):
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
    def login(request : UserRequest, db: Session):
        #TODO: 怎么记IP？
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
        return {"status": "success",
                "message": "Login successful.", 
                "user_id": user.user_id}
    
    @staticmethod
    def get_id_by_username(username:str,db: Session):
        user = db.query(DBUsers).filter(username == DBUsers.username).first()
        return user.user_id



