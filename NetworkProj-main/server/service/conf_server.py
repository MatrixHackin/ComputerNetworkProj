import base64
from typing import Dict
from websocket import WebSocket
from fastapi import WebSocket


class ConferenceServer:
    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.clients: Dict[str, WebSocket] = {}  # 维护 user_id -> WebSocket 的映射

    def get_client(self):
        return self.clients

    async def connect(self, user_id: str, websocket: WebSocket):
        """处理用户连接"""
        await websocket.accept()
        self.clients[user_id] = websocket
        print(f"User {user_id} connected to conference {self.conference_id}")

    def disconnect(self, user_id: str):
        """处理用户断开连接"""
        if user_id in self.clients:
            del self.clients[user_id]
            print(f"User {user_id} disconnected from conference {self.conference_id}")

    async def broadcast_message(self, message: str, sender_id: str):
        """广播文字消息给所有用户"""
        for user_id, connection in self.clients.items():
            if user_id != sender_id:  # 不发送给自己
                await connection.send_text(f"{sender_id}: {message}")

    async def broadcast_video(self, video_frame: bytes, sender_id: str):
        """广播视频帧给所有用户"""
        video_frame_base64 = base64.b64encode(video_frame).decode('utf-8')
        for user_id, connection in self.clients.items():
            if user_id != sender_id:  # 不发送给自己
                await connection.send_text(f"{sender_id}: video")  # 标识?
                await connection.send_text(video_frame_base64)

    async def handle_video_frame(self, video_frame: bytes, sender_id: str):
        """处理视频帧并广播"""
        await self.broadcast_video(video_frame, sender_id)

