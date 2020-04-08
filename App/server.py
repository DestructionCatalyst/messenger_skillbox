import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        decoded = data.decode('utf8').strip()
        flag = False

        print(decoded)

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                entered_login = decoded.replace("login:", "").replace("\r\n", "")

                for client in self.server.clients:
                    if client.login == entered_login:
                        self.transport.write(
                            f"Логин {entered_login} занят, попробуйте другой\r\n".encode('utf8')
                        )
                        flag = True
                        self.server.clients.remove(self)
                        self.transport.close()

                if not flag:
                    self.login = entered_login
                    self.transport.write(
                        f"Hello, {self.login}!\r\n".encode('utf8')
                    )
                    self.send_history()

            else:
                self.transport.write("Wrong login\r\n".encode('utf8'))

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\r\n"

        self.server.add_message(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for message in self.server.message_history:
            self.transport.write(message.encode())


class Server:
    clients: list
    message_history: list

    def __init__(self):
        self.clients = []
        self.message_history =[]

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()

    def add_message(self, message):
        if len(self.message_history) > 10:
            self.message_history.pop(0)
        self.message_history.append(message)





process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")