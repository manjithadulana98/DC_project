import socket
from ttypes import Node
from random import shuffle

class BootstrapServerConnection:
    def __init__(self, bs, me):
        self.bs = bs
        self.me = me
        self.users = []

    def __enter__(self):
        self.users = self.connect_to_bs()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unreg_from_bs()

    def message_with_length(self, message):
        '''
        Helper function to prepend the length of the message to the message itself
        Args:
            message (str): message to prepend the length
        Returns:
            str: Prepended message
        '''
        message = " " + message
        message = str((10000+len(message)+5))[1:] + message
        return message.encode()


    def connect_to_bs(self):
        buffer_size = 1024
        message = f"REG {self.me.ip} {self.me.port} {self.me.name}"

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.bs.ip, self.bs.port))
        s.send(self.message_with_length(message))
        data = s.recv(buffer_size)
        s.close()

        data = data.decode()
        print(f"[{self.me.name}] REG response: {data}")
        toks = data.strip().split()

        if len(toks) < 3 or toks[1] != "REGOK":
            raise RuntimeError("Registration failed")

        count = int(toks[2])
        users = []
        for i in range(count):
            offset = 3 + i * 3
            ip, port, name = toks[offset], int(toks[offset + 1]), toks[offset + 2]
            users.append(Node(ip, port, name))
        return users

    def unreg_from_bs(self):
        '''
        Unregister node at bootstrap server.
        '''
        buffer_size = 1024
        message = "UNREG " + self.me.ip + " " + str(self.me.port) + " " + self.me.name

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.bs.ip, self.bs.port))
        s.send(self.message_with_length(message))
        data = s.recv(buffer_size)
        s.close()

        toks = data.decode().split()

        if toks[1] != "UNROK":
            raise RuntimeError("Unreg failed")

        code = toks[2]
        if code == "9999":
            print(f"[{self.me.name}] UNREG failed: node not found (already unregistered)")
            return
        elif code != "0":
            raise RuntimeError(f"UNREG failed with code: {code}")




