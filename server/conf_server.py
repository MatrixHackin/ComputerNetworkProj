import asyncio

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
