import asyncio
from util import *


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


class MainServer:
    def __init__(self, server_ip, main_port):
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None
        self.conference_conns = {}  # on-going conferences
        self.conference_servers = {} # all conferences

    async def handle_create_conference(self):
        conference_id = len(self.conference_servers) + 1
        print(f"new conference id: {conference_id}")
        conference_server = ConferenceServer()
        self.conference_conns[conference_id] = conference_server
        self.conference_servers[conference_id] = conference_server
        await conference_server.start(conference_id)
        return conference_id

    def handle_join_conference(self, conference_id):
        if conference_id in self.conference_conns:
            return self.conference_conns[conference_id]
        else:
            return None

    async def handle_quit_conference(self, conference_id, writer):
        if conference_id in self.conference_conns:
            conference_server = self.conference_conns[conference_id]
            # quit_task = asyncio.create_task(conference_server.quit_conference(writer))
            await conference_server.quit_conference(writer)

    async def handle_cancel_conference(self, conference_id):
        if conference_id in self.conference_conns:
            conference_server = self.conference_conns[conference_id]
            await conference_server.cancel_conference()
            del self.conference_conns[conference_id]

    async def request_handler(self, reader, writer):
        # print('writer in request handler:')
        # print(writer)
        while True:
            data = await reader.read(100)
            message = data.decode()
            print('Received: '+message)
            if message.startswith('create'):
                conference_id = await self.handle_create_conference()
                writer.write(f'Conference {conference_id} created'.encode())
                await writer.drain()
                print(f'Create a conference with id: {conference_id}')
            elif message.startswith('join'):
                conference_id = int(message.split()[1])
                print(f"Try to join conerence {conference_id}")
                conference_server = self.handle_join_conference(conference_id)
                if conference_server:
                    print(f"Found conference {conference_id} in list")
                    writer.write(f'Joined conference {conference_id}'.encode())
                    handleClient_task = asyncio.create_task(conference_server.handle_client(reader, writer))
                else:
                    print(f"Cannot found conference {conference_id}")
                    writer.write(f'Conference {conference_id} not found'.encode())
            elif message.startswith('quit'):
                conference_id = int(message.split()[1])
                await self.handle_quit_conference(conference_id, writer)
                writer.write(f'Quit conference {conference_id}'.encode())
                await writer.drain()
                # print(self.conference_conns[conference_id].running)
                if not self.conference_conns[conference_id].running:
                    writer.write(b'Cancel this conference beacause no one still in now')
                    await writer.drain()
                    del self.conference_conns[conference_id]
                else:
                    writer.write(b'Still have people in this conference')
                    await writer.drain()
            elif message.startswith('cancel'):
                conference_id = int(message.split()[1])
                await self.handle_cancel_conference(conference_id)
                writer.write(f'Cancelled conference {conference_id}'.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def start_main_server(self):
        server = await asyncio.start_server(self.request_handler, self.server_ip, self.server_port)
        self.main_server = server
        async with server:
            await server.serve_forever()

    def start(self):
        asyncio.run(self.start_main_server())


if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    server.start()
