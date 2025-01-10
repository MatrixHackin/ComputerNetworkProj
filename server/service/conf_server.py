import base64
from typing import Dict
from websocket import WebSocket
from fastapi import WebSocket


class ConferenceServer:
    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.clients_video_msg: Dict[str, WebSocket] = {}  # 维护 user_id -> WebSocket 的映射
        self.clients_audio: Dict[str, WebSocket] = {}

    def get_client(self):
        return self.clients_video_msg

    async def connect_video_msg(self, user_id: str, websocket: WebSocket):
        """处理用户连接"""
        await websocket.accept()
        self.clients_video_msg[user_id] = websocket
        print(f"User {user_id} connected to conference {self.conference_id}")

    async def connect_audio(self, user_id: str, websocket: WebSocket):
        """处理用户连接"""
        await websocket.accept()
        self.clients_audio[user_id] = websocket
        print(f"User {user_id} connected to conference {self.conference_id}")

    def disconnect(self, user_id: str):
        """处理用户断开连接"""
        if user_id in self.clients_video_msg:
            del self.clients_video_msg[user_id]
            del self.clients_audio[user_id]
            print(f"User {user_id} disconnected from conference {self.conference_id}")

    def close(self):
        self.clients_audio.clear()  # 字典变成空的
        self.clients_video_msg.clear()

    async def broadcast_message(self, message: str, sender_id: str):
        """广播文字消息给所有用户"""
        for user_id, connection in self.clients_video_msg.items():
            if user_id != sender_id:  # 不发送给自己
                await connection.send_text(f"msg:{sender_id}: {message}")

    async def broadcast_video(self, video_frame: str, sender_id: str):
        """广播视频帧给所有用户"""
        # video_frame_base64 = base64.b64encode(video_frame).decode('utf-8')
        for user_id, connection in self.clients_video_msg.items():
            if user_id != sender_id:  # 不发送给自己
                await connection.send_text(f"video:{sender_id}:{video_frame}")

    async def handle_video_frame(self, video_frame: str, sender_id: str):
        """处理视频帧并广播"""
        await self.broadcast_video(video_frame, sender_id)

    async def broadcast_video_off(self, message: str, sender_id: str):
        """广播关闭视频帧给所有用户"""
        for user_id, connection in self.clients_video_msg.items():
            if user_id != sender_id:  # 不发送给自己
                await connection.send_text(f"video:off:{sender_id}")

    async def broadcast_audio(self, audio_data: str, sender_id: str):
        """广播音频数据给所有用户"""
        for user_id, connection in self.clients_audio.items():
            if user_id != sender_id:
                await connection.send_text(f"audio:{sender_id}:{audio_data}")

    async def broadcast_cancel(self, sender_id: str):
        """广播cancel会议给所有用户"""
        for user_id, connection in self.clients_video_msg.items():
            print(type(user_id))
            print(type(sender_id))
            print(user_id != sender_id)
            if int(user_id) != sender_id:
                await connection.send_text(f"cancel:{sender_id}")
