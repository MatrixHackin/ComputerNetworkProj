import asyncio
from util import *
from manage_db import manage_db

class ConferenceServer:
    def __init__(self):
        self.conference_id = None
        self.conf_serve_ports = None # not used?
        self.data_serve_ports = {} # not used?
        self.data_types = ['screen', 'camera', 'audio']
        self.clients_info = {}
        self.client_conns = list()
        self.mode = 'Client-Server'
        self.running = True

    async def handle_data(self, reader, writer, data_type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """
        while True:
            data = await reader.read(100)
            if not data:
                break
            if data_type == 'screen':
                data = decompress_image(data)
            for client_writer in self.client_conns:
                if client_writer != writer:
                    if data_type == 'screen':
                        data = compress_image(data)
                    client_writer.write(data)
                    await client_writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_client(self, reader, writer):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        self.client_conns.append(writer)
        print('Client_conns now:')
        print(self.client_conns)
        while self.running:
            print(f"conference {self.conference_id} listenning to a client")
            await asyncio.sleep(5)
        #     data = await reader.read(100)
        #     # TODO: after read?
        #     if not data:
        #         break
        #     # Handle client messages here
        # writer.close()
        # await writer.wait_closed()

    async def log(self):
        while self.running:
            print(f'Conference {self.conference_id} Server is running')
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """
        self.running = False
        self.client_conns.clear()
        # end the server

    async def quit_conference(self, writer):
        """
        handle quit conference request: disconnect the client from the conference
        """
        # writer.close()
        # await writer.wait_closed()
        self.client_conns.remove(writer)
        print('client_conns after quit:')
        print(self.client_conns)
        if len(self.client_conns) == 0:
            # print('Start to cancel the conference after quit')
            await self.cancel_conference()
            # print(f'state now: {self.running}')
        # TODO: if nobody in, then the conference will be closed

    async def start_server(self):
        log_task = asyncio.create_task(self.log())
        # await log_task

    async def start(self, id):
        """
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        """
        self.conference_id = id
        await self.start_server()

import datetime
import uvicorn
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel
from my_login_server import app  # 导入 FastAPI 应用实例
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, declarative_base

class Meeting(BaseModel):
    conference_id: int
    conference_name: str
    conference_password: str
    host: str

conference_servers = {} # on-going ones
meetings = [] # on-going ones
confID_count = 0
clients_ip = []
# 创建数据库处理实例
db_manager = manage_db()
Base = declarative_base()

class DBConferences(Base):
    __tablename__ = 'conferences'
    conference_id = Column(Integer, primary_key=True, index=True)
    conference_name = Column(String, index=True, unique=True) 
    host_name = Column(String, index=True)
    password = Column(String, index=True)
    port = Column(Integer, index=True)
    created_at = Column(String, index=True)
    member_num = Column(Integer, index=True)

class MainServer:
    # conference_servers = {}
    # meetings = []

    def __init__(self, server_ip, main_port):
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None
        self.clients_info = {} #如何获取？存这儿还是直接存数据库？
        global get_bd
        # self.meetings = []
        # self.id_count = 0
        # self.conference_servers = {}
    
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


    # async def handle_quit_conference(self, conference_id, writer):
    #     if conference_id in self.conference_conns:
    #         conference_server = self.conference_conns[conference_id]
    #         # quit_task = asyncio.create_task(conference_server.quit_conference(writer))
    #         await conference_server.quit_conference(writer)

    # async def handle_cancel_conference(self, conference_id):
    #     if conference_id in self.conference_conns:
    #         conference_server = self.conference_conns[conference_id]
    #         await conference_server.cancel_conference()
    #         del self.conference_conns[conference_id]

    # async def request_handler(self, reader, writer):
    #     # print('writer in request handler:')
    #     # print(writer)
    #     while True:
    #         data = await reader.read(100)
    #         message = data.decode()
    #         print('Received: '+message)
    #         if message.startswith('create'):
    #             conference_id = await self.handle_create_conference()
    #             writer.write(f'Conference {conference_id} created'.encode())
    #             await writer.drain()
    #             print(f'Create a conference with id: {conference_id}')
    #         elif message.startswith('join'):
    #             conference_id = int(message.split()[1])
    #             print(f"Try to join conerence {conference_id}")
    #             conference_server = self.handle_join_conference(conference_id)
    #             if conference_server:
    #                 print(f"Found conference {conference_id} in list")
    #                 writer.write(f'Joined conference {conference_id}'.encode())
    #                 handleClient_task = asyncio.create_task(conference_server.handle_client(reader, writer))
    #             else:
    #                 print(f"Cannot found conference {conference_id}")
    #                 writer.write(f'Conference {conference_id} not found'.encode())
    #         elif message.startswith('quit'):
    #             conference_id = int(message.split()[1])
    #             await self.handle_quit_conference(conference_id, writer)
    #             writer.write(f'Quit conference {conference_id}'.encode())
    #             await writer.drain()
    #             # print(self.conference_conns[conference_id].running)
    #             if not self.conference_conns[conference_id].running:
    #                 writer.write(b'Cancel this conference beacause no one still in now')
    #                 await writer.drain()
    #                 del self.conference_conns[conference_id]
    #             else:
    #                 writer.write(b'Still have people in this conference')
    #                 await writer.drain()
    #         elif message.startswith('cancel'):
    #             conference_id = int(message.split()[1])
    #             await self.handle_cancel_conference(conference_id)
    #             writer.write(f'Cancelled conference {conference_id}'.encode())
    #     await writer.drain()
    #     writer.close()
    #     await writer.wait_closed()

    # async def start_main_server(self):
    #     server = await asyncio.start_server(self.request_handler, self.server_ip, self.server_port)
    #     self.main_server = server
    #     async with server:
    #         await server.serve_forever()

    # def start(self):
    #     asyncio.run(self.start_main_server())


if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    server.start()
