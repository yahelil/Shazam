import socket
import threading

from scipy.spatial.distance import euclidean

from AudioUtils import extract_mfcc
from Database import *
from Encryption import Encryption
import hashlib

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 2487

def recognize_song(test_mfcc):
    """
    Recognizes a song by comparing the MFCC features of the test audio to the database.
    """
    database = Database.create_database()

    try:
        if not test_mfcc:
            raise ValueError("test_mfcc is empty or None")

        # Convert test_mfcc to a numpy array if it's not already
        test_mfcc_list = json.loads(test_mfcc)
        test_mfcc = np.array(test_mfcc_list)

        # Calculate the Euclidean distance from the test MFCC to each song's MFCC in the database
        distances = [(euclidean(test_mfcc, song_mfcc), song_name) for song_name, song_mfcc in database.items()]

        # Print the calculated distances for debugging purposes
        for distance, song_name in distances:
            print(f"Distance to {song_name}: {distance}")
        # Sort the list by distance in ascending order
        distances.sort()
        prev_name_list = [distances[0][1].split('_')[0]]
        top_3_distances = [distances[0][0]]
        top_3_matches = [distances[0][1].split('_')[0]]
        for distance, name in distances:
            if name.split('_')[0] not in prev_name_list:
                top_3_distances.append(distance)
                top_3_matches.append(name.split('_')[0])
                prev_name_list.append(name.split('_')[0])

        if top_3_distances[1] == 0:
            ratio = 0
        else:
            ratio = top_3_distances[0] / top_3_distances[1]
        Is_Dominant = ratio < 0.5
        return (top_3_matches[0], top_3_distances[0], Is_Dominant) if Is_Dominant else (top_3_matches[:3], top_3_distances[:3], Is_Dominant)
    except Exception as e:
        print(f"Error recognizing song: {e}")
        return None, None, False

class Server:

    def __init__(self):
        self.server_socket = None
        self.Encryption = {}  # dictionary: "socket: Encryption(socket)"

    @staticmethod
    def combine_funcs(*funcs):
        def combined_func(*args, **kwargs):
            for f in funcs:
                f(*args, **kwargs)

        return combined_func

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted new connection from {client_address}")
                client_handler = threading.Thread(target=self.combine_funcs(self.encryption, self.handle_client), args=(client_socket, client_address))
                client_handler.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

    def encryption(self, client_socket, a):
        self.Encryption[client_socket] = Encryption(client_socket)
        self.Encryption[client_socket].create_keys()
        self.Encryption[client_socket].send_key()
        self.Encryption[client_socket].receive_public_key()
        self.Encryption[client_socket].create_box()

    def handle_client(self, client_socket, client_address):
        print(f"New connection: {client_address}")
        try:
            while True:
                message = self.Encryption[client_socket].decrypt()
                if message == "Failed To Decrypt":
                    break
                self.process_message(client_socket, message)
        except ConnectionAbortedError:
            print(f"{client_address} disconnected")
        finally:
            print(f"Connection closed: {client_address}")
            self.Encryption.pop(client_socket)
            client_socket.close()

    def process_message(self, client_socket, message):
        if message.startswith('REGISTER'):
            self.register_client(client_socket, message)
        elif message.startswith('ASSIGN'):
            self.assign_client(client_socket, message)
        else:
            self.calculate_sample(client_socket, message)

    def register_client(self, client_socket, message):
        try:
            _, client_name, client_password = message.split()
        except ValueError:
            self.Encryption[client_socket].send_encrypted_msg("Invalid format. Use REGISTER <username> <password>".encode('utf-8'))
            return
        if not client_name or not client_password:
            self.Encryption[client_socket].send_encrypted_msg("Username and password cannot be empty".encode('utf-8'))
            return
        clients = Database.get_clients_database()
        registered = False
        for client in clients:
            print(f"{client[1] =}, {client[2] =}")
            if (client_name, hashlib.md5(client_password.encode()).hexdigest()) == (client[1], client[2]):
                self.Encryption[client_socket].send_encrypted_msg(f"{client_name} already registered".encode('utf-8'))
                registered = True
        if not registered:
            Database.update_clients_database(client_name, client_password)
            self.Encryption[client_socket].send_encrypted_msg(f"Registered as {client_name}".encode('utf-8'))

    def assign_client(self, client_socket, message):
        try:
            client_name, client_password = message.split()[1:3]
        except ValueError:
            self.Encryption[client_socket].send_encrypted_msg("Invalid format. Use ASSIGN <username> <password>".encode('utf-8'))
            return
        clients = Database.get_clients_database()
        for client in clients:
            if (client_name, hashlib.md5(client_password.encode()).hexdigest()) == (client[1], client[2]):
                self.Encryption[client_socket].send_encrypted_msg("Connection APPROVED".encode('utf-8'))
                return

    def calculate_sample(self, client_socket, test_mfcc):
        if test_mfcc is not None:
            recognized_song, distances, Is_Dominant = recognize_song(test_mfcc)
            self.Encryption[client_socket].send_encrypted_msg(f'Is_Dominant: {Is_Dominant}\nThe recognized song is: {recognized_song}\nThe distances are: {distances}'.encode("utf-8"))
        else:
            self.Encryption[client_socket].send_encrypted_msg("Error processing audio sample".encode("utf-8"))

if __name__ == "__main__":
    s = Server()
    s.start()