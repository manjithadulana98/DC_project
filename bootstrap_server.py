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
        '''
        Register node at bootstrap server.
        Args:
            bs (Node): Bootstrap server node
            me (Node): This node
        Returns:
            list(Node) : List of other nodes in the distributed system
        Raises:
            RuntimeError: If server sends an invalid response or if registration is unsuccessful
        '''
        buffer_size = 1024
        message = "REG " + self.me.ip + " " + str(self.me.port) + " " + self.me.name

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.bs.ip, self.bs.port))
        s.send(self.message_with_length(message))
        data = s.recv(buffer_size)
        s.close()

        data = data.decode()
        print(data)

        toks = data.strip().split()

        if len(toks) < 3 or toks[1] != "REGOK":
            raise RuntimeError("Registration failed")

        try:
            count = int(toks[2])
        except ValueError:
            raise RuntimeError("Invalid REGOK response")

        if count == 0:
            return []
        elif count == 1:
            return [Node(toks[3], int(toks[4]), toks[5])]
        elif count == 2:
            return [
                Node(toks[3], int(toks[4]), toks[5]),
                Node(toks[6], int(toks[7]), toks[8])
            ]
        else:
            raise RuntimeError("Unexpected peer count")

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

