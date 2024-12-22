import asyncio
from util import *
import datetime
import uvicorn
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, declarative_base
from 

conference_servers = {} # on-going ones
meetings = [] # on-going ones
confID_count = 0
clients_ip = []

class MainServer:
    def __init__(self, server_ip, main_port):
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None
        self.clients_info = {} #如何获取？存这儿还是直接存数据库？
    
    @app.post("/user/create-meeting")
    async def create_meeting(request: Request, db: Session = Depends(db_manager.get_db)):
        # 获取请求体中的 JSON 数据
        payload = await request.json()
        # 获取请求头, 目前没有使用
        headers = request.headers

        # TODO：维护client IP列表？？
        client_ip = request.client.host
        client_port = request.client.port
        print(client_ip)
        print(client_port)
        
        print('enter create')
        # 检查会议是否已经存在
        for existing_meeting in meetings:
            if existing_meeting["conference_name"] == payload["conference_name"]:
                return {"status": "fail",
                        "message": "Conference already exist."}

        global confID_count
        conf_id = confID_count ## TODO:在数据库中设置为自增？
        print(f'create new conference {conf_id}')
        confID_count += 1
        conference_server = ConferenceServer()

        # 将会议添加到列表
        meetings.append({
            "conference_id": conf_id,
            "conference_name": payload["conference_name"],
            "conference_password": payload["conference_password"],
            "host": payload["host"]
        })
        print('meetings now:')
        print(meetings)

        new_conf = DBConferences(conference_id = conf_id,
                                conference_name = payload["conference_name"],
                                host_name = payload["host"],  #似乎只传name
                                password = payload["conference_password"],
                                port = 9001,  #TODO:还是每个会有一个单独的port
                                created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                                member_num = 0)
        db.add(new_conf)
        db.commit()
        db.refresh(new_conf)

        conference_servers[conf_id] = conference_server
        await conference_server.start(conf_id)
        return {"status": "success", 
                "conference_id": conf_id,
                "port": 9001,
                "message": "Conference created successfully."}
    
    @app.post("/user/join-meeting")
    async def create_meeting(request: Request):
        # 获取请求体中的 JSON 数据
        payload = await request.json()
        # 获取请求头, 目前没有使用
        headers = request.headers

        client_ip = request.client.host
        client_port = request.client.port

        find_conf = False
        conference_id = 0
        for existing_meeting in meetings:
            if existing_meeting["conference_name"] == payload["conference_name"]:
                find_conf = True
                conference_id = existing_meeting["conference_id"]
                if existing_meeting["conference_password"] == payload["conference_password"]:
                    break
                else:
                    return {"status": "fail",
                            "message": "Wrong password."}

        if find_conf:
            conference_server = conference_servers[conference_id]
            # 如何检查是否已加入会议，入会用户信息存在哪里？
            if False:
                return {"status": "fail",
                        "message": "Already in conference."}
            else:
                # 加入会议
                clients_ip.append(client_ip)
                pass
        else:
            return {"status": "fail",
                    "message": "Invalid conference name."}
        
        return {"status": "success", 
                "message": "Join conference successfully."}

    def start(slef):
        uvicorn.run(app, host=SERVER_IP, port=MAIN_SERVER_PORT)

if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    server.start()
