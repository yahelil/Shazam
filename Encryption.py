import nacl
from nacl import public
from protocol import Protocol
from nacl.public import Box, PrivateKey, PublicKey
from nacl.utils import random


class Encryption:
    def __init__(self, socket):
        self.box = None
        self.socket = socket
        self.private_key = None
        self.public_key = None
        self.receiver_public_key = None
        self.prot = Protocol(self.socket)
        self.public_key_bytes = None
        self.private_key_bytes = None

    def create_keys(self):
        # Generate private key
        self.private_key = public.PrivateKey.generate()
        self.public_key = self.private_key.public_key

        # Convert private key to bytes
        self.private_key_bytes = bytes(self.private_key)
        self.public_key_bytes = bytes(self.public_key)

    def decrypt(self):
        encrypted_message = self.prot.get_msg()[1]
        if not encrypted_message:
            return "Failed To Decrypt"
        # Ensure receiver_public_key is set before decryption
        if not self.receiver_public_key:
            raise ValueError("Receiver public key not set.")
        if not isinstance(self.private_key, PrivateKey):
            raise TypeError("self.private_key must be a PrivateKey.")
        if not isinstance(self.receiver_public_key, PublicKey):
            raise TypeError("self.receiver_public_key must be a PublicKey.")

        try:
            decrypted_message = self.box.decrypt(encrypted_message)
            print(f"{decrypted_message =}")
            return decrypted_message.decode('utf-8')
        except nacl.exceptions.ValueError as e:
            print(f"connection error: {e}")
            return "connection error"

    def send_key(self):
        # Serialize public key to send it over the network
        public_key_bytes = self.public_key.__bytes__()
        msg = self.prot.create_msg(public_key_bytes)
        self.socket.send(msg)

    def receive_public_key(self):
        public_key_bytes = self.prot.get_msg()[1]
        if len(public_key_bytes) != 32:
            raise ValueError("Public key must be 32 bytes.")
        self.receiver_public_key = PublicKey(public_key_bytes)

    def create_msg(self, msg) -> bytes:
        # Generate a nonce of 24 bytes
        nonce = random(Box.NONCE_SIZE)

        # Encrypt the message with the generated nonce
        encrypted_msg = self.box.encrypt(msg, nonce)

        # Return nonce + ciphertext
        return encrypted_msg

    def send_encrypted_msg(self, msg):
        encrypted_msg = self.create_msg(msg)
        msg = self.prot.create_msg(encrypted_msg)
        self.socket.send(msg)

    def create_box(self):
        self.box = Box(self.private_key, self.receiver_public_key)