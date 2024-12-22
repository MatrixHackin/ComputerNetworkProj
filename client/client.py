import asyncio
import json

class ConferenceClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.user_id=None
        self.reader = None
        self.writer = None

    async def start(self):
       pass 
