class Protocol:
    MESSAGE_LENGTH = 10

    def __init__(self, c_s):
        self.current_socket = c_s

    def get_msg(self) -> (bool, bytes):
        data = self.current_socket.recv(Protocol.MESSAGE_LENGTH)
        if data == b"":
            return False, "Connection Error".encode('utf-8')

        try:
            datalen = int(data.decode().strip())
        except ValueError:
            return False, "Message Error".encode('utf-8')

        data = self.current_socket.recv(datalen)
        if data == b"":
            return False, "Connection Error".encode('utf-8')

        while len(data) < datalen:
            extra = self.current_socket.recv(datalen - len(data))
            if extra == b"":
                return False, "Connection Error".encode('utf-8')
            data += extra

        return True, data

    def create_msg(self, data: bytes):
        datalen = len(data)
        msg = str(datalen).zfill(self.MESSAGE_LENGTH).encode() + data
        return msg
