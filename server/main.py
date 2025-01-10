from typing import Dict

from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn
from sqlalchemy.orm import Session
from server.service.main_server import MainServer
from server.model.database_init import ManageDB
from server.service.user_service import UserRequest, UserService
app = FastAPI()
import asyncio

# 创建数据库处理实例
db_manager = ManageDB()

main_server = MainServer()

# 创建用户管理实例，并注入数据库获取函数
user_manager = UserService(db_manager.get_db)

#onference_manager = ConferenceService(db_manager.get_db)

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
    # TODO: 存client的ip用于广播？
    return user_manager.login(user, db)

@app.post("/user/create-meeting")
async def create_meet(request: Request):
    # 获取请求体中的 JSON 数据
    #TODO: 存client_lsit，每次新建会议都广播一次get_canjoin_conferencelist()？
    payload = await request.json()
    conference_name=payload["conference_name"]
    conference_password=payload["conference_password"]
    conference_hostid=payload["host_id"]
    new_server=main_server.create_meeting(conference_name,conference_password,conference_hostid)
    #await main_server.broadcast("update")
    return {"status": "success",
            "message": "created"}

@app.post("/user/join-meeting")
async def join_meet(request: Request):
    # 获取请求体中的 JSON 数据
    payload = await request.json()
    user_id=payload["user_id"]
    conference_name=payload["conference_name"]
    conference_password=payload["conference_password"]
    conf_id=main_server.join_meeting(user_id,conference_name,conference_password)
    print(conf_id)
    await main_server.broadcast("update")
    return {"status": "success",
            "message": "joined",
            "conference_id": conf_id}

@app.get("/user/{user_id}/canjoin-meeting-list")
async def get_canjoin_meetinglist(request: Request):
    user_id=request.path_params["user_id"]
    conference_list=main_server.get_canjoin_conferencelist(user_id)
    return {"status": "success","data": conference_list}

@app.get("/user/{user_id}/joined-meeting-list")
async def get_joined_meetinglist(request: Request):
    user_id=request.path_params["user_id"]
    conference_list=main_server.get_joined_conferencelist(user_id)
    return {"status": "success","data": conference_list}

@app.websocket("/ws/{conference_id}/{user_id}/video_msg")
async def websocket_endpoint_video_msg(websocket: WebSocket, conference_id: str, user_id: str):
    """每个用户连接到指定会议"""
    print("进入ws_video_msg")
    print(main_server.confereces)
    conference_server = main_server.confereces[int(conference_id)]["server"]  # 获取会议实例
    await conference_server.connect_video_msg(user_id, websocket)  # 用户连接到会议
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            # print(f"Message from {user_id} in conference {conference_id}: {data}")

            # 如果是广播消息，转发给其他用户
            if data.startswith("broadcast:"):
                print(conference_server.get_client(), "广播成功")
                await conference_server.broadcast_message(data[len("broadcast:"):], user_id)
            elif data.startswith("video:"):
                # 如果是视频帧，处理并广播
                await conference_server.handle_video_frame(data[len("video:"):], user_id)
            elif data.startswith("video:off"):
                # 如果是关闭视频帧，广播关闭视频帧
                print("视频")
                await conference_server.broadcast_video_off(data, user_id)
                print("关闭视频帧")
            else:
                print(f"Unknown message type from {user_id}: {data}")
    except WebSocketDisconnect:
        conference_server.disconnect(user_id)  # 处理用户断开连接

@app.websocket("/ws/{conference_id}/{user_id}/audio")
async def websocket_endpoint_audio(websocket: WebSocket, conference_id: str, user_id: str):
    """每个用户连接到指定会议"""
    print("进入ws_audio")
    print(main_server.confereces)
    conference_server = main_server.confereces[int(conference_id)]["server"]  # 获取会议实例
    await conference_server.connect_audio(user_id, websocket)  # 用户连接到会议
    try:
        while True:
            # 接收客户端消息
            #websocket.send
            data = await websocket.receive_text()
            if data.startswith("audio:"):
                # 如果是音频数据，广播给其他用户
                await conference_server.broadcast_audio(data[len("audio:"):], user_id)
            else:
                print(f"Unknown message type from {user_id}: {data}")
    except WebSocketDisconnect:
        conference_server.disconnect(user_id)  # 处理用户断开连接

@app.post("/user/quit-meeting")
async def quit_meet(request: Request):
    # 获取请求体中的 JSON 数据
    try:
        payload = await request.json()
        user_id = payload["user_id"]
        conference_id = payload["conference_id"]
        # print(f"用户id:{user_id}")
        # print(f"会议id:{conference_id}")
    except:
        return {"status": "failed",
                "message": "invalid request body"}
    main_server.quit_meeting(user_id, conference_id)
    print(f'{main_server.confereces}')
    return {"status": "success",
            "message": "quit"}

@app.post("/user/cancel-meeting")
async def cancel_meet(request: Request):
    # 获取请求体中的 JSON 数据
    try:
        payload = await request.json()
        user_id = payload["user_id"]
        conference_id = payload["conference_id"]
        print(f"用户id:{user_id}")
        print(f"会议id:{conference_id}")
    except:
        return {"status": "failed",
                "message": "invalid request body"}
    print("label0")
    can_cancel = main_server.check_auth(user_id, conference_id)
    print("label")
    if can_cancel:
        await main_server.confereces[conference_id]["server"].broadcast_cancel(user_id)
        main_server.cancel_meeting(conference_id)
        await main_server.broadcast("update")
        return {"status": "success",
                "message": "cancel"}
    else:
        return {"status": "failed",
                "message": "You are not the host, cannot cancel this conference."}
    
@app.websocket("/wsconnect")
async def websocket_connect(websocket: WebSocket):
    print("connected request")
    await main_server.websocket_connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await main_server.websocket_disconnect(websocket)

# 主程序启动入口
if __name__ == "__main__":
    uvicorn.run(app, host="10.26.194.204", port=8888)
