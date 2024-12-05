import asyncio
from util import *
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import threading


class ConferenceClient:
    def __init__(self):
        self.is_working = True
        self.server_addr = (SERVER_IP, MAIN_SERVER_PORT)
        self.on_meeting = False
        self.conns = {}  # what should be stored here?
        self.support_data_types = ['screen', 'camera', 'audio']
        self.share_data = {}
        self.in_conference = list()
        self.handle_conference = list()
        self.recv_data = {}
        self.reader = None
        self.writer = None

    async def create_conference(self):
        try:
            self.writer.write(b'create')
            await self.writer.drain()
            response = await self.reader.read(100)
            print(response.decode())
            conference_id = response.decode().split(" ")[1].strip()
            self.handle_conference.append(conference_id)
            await self.join_conference(conference_id)
        except Exception as e:
            print(f"Failed to create conference: {e}")

    async def join_conference(self, conference_id):
        if conference_id not in self.in_conference:
            try:
                self.writer.write(f'join {conference_id}'.encode())
                await self.writer.drain()
                response = await self.reader.read(100)
                print(response.decode())
                if response.decode().split(" ")[0].strip()=="Joined":
                    print("conference exist")
                    self.on_meeting = True
                    self.in_conference.append(conference_id)
                else:
                    print("conference not exist")
            except Exception as e:
                print(f"Failed to join conference {conference_id}: {e}")
        else:
            print('You are already in the conference ')

    async def quit_conference(self, conference_id):
        if conference_id in self.in_conference:
            try:
                self.writer.write(f'quit {conference_id}'.encode())
                # await self.writer.drain()
                # response = await self.reader.read(100)
                print(response.decode())
                self.in_conference.remove(conference_id)
                if len(self.in_conference) == 0:
                    self.on_meeting = False
                # TODO: how to deal with handle_conference???
                response = await self.reader.read(100)
                print(response.decode())
                if response.decode().startswith('Cancel'):
                    self.handle_conference.remove(conference_id)
            except Exception as e:
                print(f"Failed to quit conference {conference_id}: {e}")
        else:
            print('You are not in this conference now')

    async def cancel_conference(self, conference_id):
        if conference_id in self.handle_conference:
            try:
                if conference_id in self.in_conference:
                    self.in_conference.remove(conference_id)
                self.writer.write(f'cancel {conference_id}'.encode())
                await self.writer.drain()
                response = await self.reader.read(100)
                print(response.decode())
                self.handle_conference.remove(conference_id)
                if len(self.in_conference) == 0:
                    self.on_meeting = False
            except Exception as e:
                print(f"Failed to cancel conference {conference_id}: {e}")
        else:
            print('You are not allowed to cancel this conference')

    def keep_share(self, data_type, send_conn, capture_function, compress=None, fps_or_frequency=30):
        while self.on_meeting:
            data = capture_function()
            if compress:
                data = compress(data)
            send_conn.write(data)
            asyncio.run(send_conn.drain())
            asyncio.sleep(1 / fps_or_frequency)

    def share_switch(self, data_type):
        if data_type in self.share_data:
            self.share_data[data_type] = not self.share_data[data_type]

    def keep_recv(self, recv_conn, data_type, decompress=None):
        while self.on_meeting:
            data = asyncio.run(recv_conn.read(100))
            if decompress:
                data = decompress(data)
            self.recv_data[data_type] = data

    def output_data(self):
        for data_type, data in self.recv_data.items():
            if data_type == 'screen':
                # Display screen data
                pass
            elif data_type == 'camera':
                # Display camera data
                pass
            elif data_type == 'audio':
                # Play audio data
                pass

    def close_conference(self):
        if len(self.in_conference) == 0:
            self.on_meeting = False
        # Close connections and cancel tasks

    async def main(self):
        self.reader, self.writer = await asyncio.open_connection(*self.server_addr)
        while True:
            if not self.on_meeting:
                status = 'Free'
            else:
                status = f'OnMeeting-{self.in_conference}'

            recognized = True
            cmd_input = input(f'({status}) Please enter a operation (enter "?" to help): ').strip().lower()
            fields = cmd_input.split(maxsplit=1)
            if len(fields) == 1:
                if cmd_input in ('?', '？'):
                    print(HELP)
                elif cmd_input == 'create':
                    await self.create_conference()
                else:
                    recognized = False
            elif len(fields) == 2:
                if fields[0] == 'join':
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        await self.join_conference(input_conf_id)
                    else:
                        print('[Warn]: Input conference ID must be in digital form')
                elif fields[0] == 'quit':
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        await self.quit_conference(input_conf_id)
                    else:
                        print('[Warn]: Input conference ID must be in digital form')
                elif fields[0] == 'cancel':
                    input_conf_id = fields[1]
                    if input_conf_id.isdigit():
                        await self.cancel_conference(input_conf_id)
                    else:
                        print('[Warn]: Input conference ID must be in digital form')
                elif fields[0] == 'switch': # what is this for?
                    data_type = fields[1]
                    if data_type in self.share_data.keys():
                        self.share_switch(data_type)
                else:
                    recognized = False
            else:
                recognized = False

            if not recognized:
                print(f'[Warn]: Unrecognized cmd_input {cmd_input}')

    def start(self):
        asyncio.run(self.main())


if __name__ == '__main__':
    client1 = ConferenceClient()
    client1.start()
