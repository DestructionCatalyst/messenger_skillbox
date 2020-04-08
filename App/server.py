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

        print(decoded)

        if self.login is not None:
            if decoded.startswith("private"):
                self.send_private_message(decoded.replace("private", "").strip())
            else:
                self.send_message(decoded)
        else:
            self.check_login(decoded)

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def check_login(self, decoded):

        if decoded.startswith("login:"):
            entered_login = decoded.replace("login:", "").replace("\r\n", "")

            for client in self.server.clients:
                if client.login == entered_login:
                    self.transport.write(
                        f"Логин {entered_login} занят, попробуйте другой\r\n".encode('utf8')
                    )
                    self.transport.close()

            self.login = entered_login
            self.transport.write(
                f"Hello, {self.login}!\r\n".encode('utf8')
            )
            self.send_history()
        else:
            self.transport.write("Wrong login\r\n".encode('utf8'))

    def send_message(self, content: str):
        message = f"{self.login}: {content}\r\n"

        self.server.add_message(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for message in self.server.message_history:
            self.transport.write(message.encode())

    def send_private_message(self, content: str):
        target = content[0:content.find(" ")]
        found = False

        for client in self.server.clients:
            if client.login == target:
                content.replace(client.login, "").strip()
                client.transport.write(
                    f"{self.login} (private): {content}\r\n".encode()
                )
                found = True
        if not found:
            self.transport.write(f"Пользователь с ником {target} не найден!\r\n".encode())


class Server:
    clients: list
    admins: list
    message_history: list

    def __init__(self):
        self.clients = []
        self.message_history = []
        self.admins = ["Admin"]

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